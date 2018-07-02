import io
import pytest
import structlog
import structlog.stdlib
import scopedlog
import scopedlog.sink_structlog
import scopedlog.idgen_seq


@pytest.fixture
def strio():
    return io.StringIO()


@pytest.fixture
def slog(strio):
    log = structlog.wrap_logger(
        structlog.PrintLogger(file=strio),
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer(sort_keys=True)
        ]
    )

    scopedlog.idgen_seq.SeqScopeIdGenenerator._counters._counters = dict()

    slog = scopedlog.ScopedLog(
        sink=scopedlog.sink_structlog.StructlogSink(log),
        id_gen=scopedlog.idgen_seq.SeqScopeIdGenenerator()
    )

    return slog


def test_empty(slog, strio):
    with slog.info("empty1"):
        pass

    with slog.debug("empty2"):
        pass

    assert strio.getvalue() == """
{"event": "empty1", "level": "info", "scope_id": 1, "scope_state": "enter"}
{"event": "empty1", "level": "info", "scope_id": 1, "scope_state": "exit", "scope_status": "success"}
{"event": "empty2", "level": "debug", "scope_id": 1, "scope_state": "enter"}
{"event": "empty2", "level": "debug", "scope_id": 1, "scope_state": "exit", "scope_status": "success"}
""".lstrip()


def test_kw(slog, strio):
    with slog.info("one", a=1, b=2) as sl:
        sl.exit_kw.update(c=3, d=4)

    assert strio.getvalue() == """
{"a": 1, "b": 2, "event": "one", "level": "info", "scope_id": 1, "scope_state": "enter"}
{"c": 3, "d": 4, "event": "one", "level": "info", "scope_id": 1, "scope_state": "exit", "scope_status": "success"}
""".lstrip()


def test_failure(slog, strio):
    with slog.info("one", a=1, b=2) as sl:
        sl.fail(c=3, d=4)

    assert strio.getvalue() == """
{"a": 1, "b": 2, "event": "one", "level": "info", "scope_id": 1, "scope_state": "enter"}
{"c": 3, "d": 4, "event": "one", "level": "error", "scope_id": 1, "scope_state": "exit", "scope_status": "failure"}
""".lstrip()


def test_extra_logs(slog, strio):
    with slog.info("one", a=1, b=2) as sl:
        sl.info("step1", e=5)
        sl.warn("step2", f=6)
        sl.debug("step3", g=7)

    assert strio.getvalue() == """
{"a": 1, "b": 2, "event": "one", "level": "info", "scope_id": 1, "scope_state": "enter"}
{"e": 5, "event": "one", "level": "info", "scope_id": 1, "scope_state": "step1"}
{"event": "one", "f": 6, "level": "warning", "scope_id": 1, "scope_state": "step2"}
{"event": "one", "g": 7, "level": "debug", "scope_id": 1, "scope_state": "step3"}
{"event": "one", "level": "info", "scope_id": 1, "scope_state": "exit", "scope_status": "success"}
""".lstrip()


def test_exception(slog, strio):
    with pytest.raises(RuntimeError):
        with slog.info("one", a=1, b=2) as sl:
            sl.info("step1", e=5)
            sl.exit_kw.update(c=3, d=4)
            exception = RuntimeError("error")
            raise exception

    assert strio.getvalue().strip() == """
{"a": 1, "b": 2, "event": "one", "level": "info", "scope_id": 1, "scope_state": "enter"}
{"e": 5, "event": "one", "level": "info", "scope_id": 1, "scope_state": "step1"}
{"c": 3, "d": 4, "event": "one", "exc_info": "RuntimeError('error',)", "level": "error", "scope_id": 1, "scope_state": "exit", "scope_status": "exception"}
""".strip()  # noqa: E501
