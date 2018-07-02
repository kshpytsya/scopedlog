import pytest
import scopedlog
import scopedlog.idgen_seq
import scopedlog.idgen_uuid
import uuid


class CollectingScopedLogSink(scopedlog.ScopedLogSink):
    def __init__(self):
        self.collected = []


CollectingScopedLogSink.__abstractmethods__ = set(CollectingScopedLogSink.__abstractmethods__)
for i in """
log_debug
log_info
log_warn
log_error
log_exception
""".split():
    def one(name):
        def log_xxx(self, *args):
            self.collected.append((name, args))

        setattr(CollectingScopedLogSink, name, log_xxx)
        CollectingScopedLogSink.__abstractmethods__.remove(name)

    one(i)
CollectingScopedLogSink.__abstractmethods__ = frozenset(CollectingScopedLogSink.__abstractmethods__)


@pytest.fixture
def idgen():
    scopedlog.idgen_seq.GlobalSeqScopeIdGenenerator._counter._value = 0
    return scopedlog.idgen_seq.GlobalSeqScopeIdGenenerator()


def idgen_per_scope():
    scopedlog.idgen_seq.SeqScopeIdGenenerator._counters._counters = dict()
    return scopedlog.idgen_seq.SeqScopeIdGenenerator()


class UnimportantException(Exception):
    pass


@pytest.fixture
def slog(idgen):
    return scopedlog.ScopedLog(
        sink=CollectingScopedLogSink(),
        id_gen=idgen,
        unimportant_exceptions=(UnimportantException,)
    )


@pytest.mark.parametrize(
    'idgen,id1,id2',
    [
        [idgen(), 1, 2],
        [idgen_per_scope(), 1, 1],
        [scopedlog.idgen_uuid.Uuid1ScopeIdGenerator(), "uuid1-1", "uuid1-2"],
        [scopedlog.idgen_uuid.Uuid4ScopeIdGenerator(), "uuid4-1", "uuid4-2"],
    ]
)
def test_empty(slog, monkeypatch, id1, id2):
    with monkeypatch.context() as mp:
        counter = 0

        def uuid1():
            nonlocal counter
            counter += 1
            return "uuid1-%d" % counter

        mp.setattr(uuid, "uuid1", uuid1)

        def uuid4():
            nonlocal counter
            counter += 1
            return "uuid4-%d" % counter

        mp.setattr(uuid, "uuid4", uuid4)

        with slog.info("empty1"):
            pass

        with slog.debug("empty2"):
            pass

        assert slog.sink.collected == [
            ("log_info", ("empty1", {"scope_id": id1, "scope_state": "enter"})),
            ("log_info", ("empty1", {"scope_id": id1, "scope_status": "success", "scope_state": "exit"})),
            ("log_debug", ("empty2", {"scope_id": id2, "scope_state": "enter"})),
            ("log_debug", ("empty2", {"scope_id": id2, "scope_status": "success", "scope_state": "exit"}))
        ]


def test_kw(slog):
    with slog.info("one", a=1, b=2) as sl:
        sl.exit_kw.update(c=3, d=4)

    assert slog.sink.collected == [
        ("log_info", ("one", {"scope_id": 1, "a": 1, "b": 2, "scope_state": "enter"})),
        ("log_info", ("one", {"scope_id": 1, "c": 3, "d": 4, "scope_status": "success", "scope_state": "exit"}))
    ]


def test_failure(slog):
    with slog.info("one", a=1, b=2) as sl:
        sl.fail(c=3, d=4)

    assert slog.sink.collected == [
        ("log_info", ("one", {"scope_id": 1, "a": 1, "b": 2, "scope_state": "enter"})),
        ("log_error", ("one", {"scope_id": 1, "c": 3, "d": 4, "scope_status": "failure", "scope_state": "exit"}))
    ]


def test_extra_logs(slog):
    for f in [slog.info, slog.debug]:
        with f("one", a=1, b=2) as sl:
            sl.info("step1", e=5)
            sl.warn("step2", f=6)
            sl.debug("step3", g=7)

    assert slog.sink.collected == [
        ("log_info", ("one", {"scope_id": 1, "a": 1, "b": 2, "scope_state": "enter"})),
        ("log_info", ("one", {"scope_id": 1, "e": 5, "scope_state": "step1"})),
        ("log_warn", ("one", {"scope_id": 1, "f": 6, "scope_state": "step2"})),
        ("log_debug", ("one", {"scope_id": 1, "g": 7, "scope_state": "step3"})),
        ("log_info", ("one", {"scope_id": 1, "scope_status": "success", "scope_state": "exit"})),

        ("log_debug", ("one", {"scope_id": 2, "a": 1, "b": 2, "scope_state": "enter"})),
        ("log_debug", ("one", {"scope_id": 2, "e": 5, "scope_state": "step1"})),
        ("log_warn", ("one", {"scope_id": 2, "f": 6, "scope_state": "step2"})),
        ("log_debug", ("one", {"scope_id": 2, "g": 7, "scope_state": "step3"})),
        ("log_debug", ("one", {"scope_id": 2, "scope_status": "success", "scope_state": "exit"}))
    ]


def test_exception(slog):
    with pytest.raises(RuntimeError):
        with slog.info("one", a=1, b=2) as sl:
            sl.info("step1", e=5)
            sl.exit_kw.update(c=3, d=4)
            exception = RuntimeError("error")
            raise exception

    assert slog.sink.collected[2][1][1]["scope_exception"] is exception
    slog.sink.collected[2][1][1]["scope_exception"] = ""

    assert slog.sink.collected == [
        ("log_info", ("one", {"scope_id": 1, "a": 1, "b": 2, "scope_state": "enter"})),
        ("log_info", ("one", {"scope_id": 1, "e": 5, "scope_state": "step1"})),
        (
            "log_exception",
            (
                "one",
                {
                    "scope_id": 1,
                    "c": 3,
                    "d": 4,
                    "scope_exception": "",
                    "scope_state": "exit",
                    "scope_status": "exception"
                }
            )
        )
    ]


def test_unimportant_exception(slog):
    exceptions = []
    for f in [slog.info, slog.debug]:
        with pytest.raises(UnimportantException):
            with f("one"):
                exceptions.append(UnimportantException())
                raise exceptions[-1]

    for i, exception in enumerate(exceptions):
        assert slog.sink.collected[1 + 2 * i][1][1]["scope_exception"] is exceptions[i]
        slog.sink.collected[1 + 2 * i][1][1]["scope_exception"] = ""

    assert slog.sink.collected == [
        ("log_info", ("one", {"scope_id": 1, "scope_state": "enter"})),
        (
            "log_info",
            (
                "one",
                {"scope_id": 1, "scope_exception": "", "scope_state": "exit", "scope_status": "exception"}
            )
        ),
        ("log_debug", ("one", {"scope_id": 2, "scope_state": "enter"})),
        (
            "log_debug",
            (
                "one",
                {"scope_id": 2, "scope_exception": "", "scope_state": "exit", "scope_status": "exception"}
            )
        )
    ]
