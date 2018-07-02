import abc as _abc
import contextlib as _contextlib

try:
    __version__ = __import__('pkg_resources').get_distribution(__name__).version
except:  # noqa # pragma: no cover
    pass


class ScopedLogSink(_abc.ABC):
    @_abc.abstractmethod
    def log_debug(self, scope_name, scope_id, scope_state, state_kw):
        pass  # pragma: no cover

    @_abc.abstractmethod
    def log_info(self, scope_name, scope_id, scope_state, state_kw):
        pass  # pragma: no cover

    @_abc.abstractmethod
    def log_warn(self, scope_name, scope_id, scope_state, state_kw):
        pass  # pragma: no cover

    @_abc.abstractmethod
    def log_error(self, scope_name, scope_id, state_kw):
        pass  # pragma: no cover

    @_abc.abstractmethod
    def log_exception(self, scope_name, scope_id, state_kw, exc_info):
        pass  # pragma: no cover


class ScopedLogIdGenerator(_abc.ABC):
    @_abc.abstractmethod
    def __call__(self, scope_name):
        pass  # pragma: no cover


class ScopedLogContext(_contextlib.AbstractContextManager):
    def __init__(self, _parent, scope_id, scope_name, enter_kw, low):
        self._parent = _parent
        self._scope_id = scope_id
        self._scope_name = scope_name
        self._enter_kw = enter_kw
        self._failed = False
        self._entered = False

        if low:
            self._log_info = self._parent.sink.log_debug
        else:
            self._log_info = self._parent.sink.log_info

        self.exit_kw = dict()

    def _fill_kw(self, d, state, **kw):
        d.update(kw)
        d["scope_state"] = state
        d["scope_id"] = self._scope_id

    def __enter__(self):
        assert not self._entered
        self._entered = True

        self._fill_kw(self._enter_kw, "enter")
        self._log_info(self._scope_name, self._enter_kw)

        return self

    def __exit__(self, *exc_info):
        assert self._entered

        self._fill_kw(self.exit_kw, "exit")

        if exc_info[0] is None:
            if self._failed:
                self.exit_kw["scope_status"] = "failure"
                log_f = self._parent.sink.log_error
            else:
                self.exit_kw["scope_status"] = "success"
                log_f = self._log_info

        else:
            self.exit_kw["scope_status"] = "exception"
            self.exit_kw["scope_exception"] = exc_info[1]

            if self._parent.is_unimportant_exception(exc_info[0]):
                log_f = self._log_info
            else:
                log_f = self._parent.sink.log_exception

        log_f(self._scope_name, self.exit_kw)

    def fail(self, **kw):
        self._failed = True
        self.exit_kw.update(kw)

    def info(self, state, **state_kw):
        self._fill_kw(state_kw, state)
        self._log_info(self._scope_name, state_kw)

    def debug(self, state, **state_kw):
        self._fill_kw(state_kw, state)
        self._parent.sink.log_debug(self._scope_name, state_kw)

    def warn(self, state, **state_kw):
        self._fill_kw(state_kw, state)
        self._parent.sink.log_warn(self._scope_name, state_kw)


class ScopedLog:
    def __init__(
        self,
        *,
        sink,
        id_gen,
        unimportant_exceptions=tuple(),
        context_factory=ScopedLogContext
    ):
        assert isinstance(sink, ScopedLogSink)
        assert isinstance(id_gen, ScopedLogIdGenerator)

        self.sink = sink
        self.id_gen = id_gen
        self.unimportant_exceptions = unimportant_exceptions
        self.context_factory = context_factory

    def info(self, scope_name, **enter_kw):
        return self.context_factory(self, self.id_gen(scope_name), scope_name, enter_kw, False)

    def debug(self, scope_name, **enter_kw):
        return self.context_factory(self, self.id_gen(scope_name), scope_name, enter_kw, True)

    def is_unimportant_exception(self, exc_type):
        return issubclass(exc_type, self.unimportant_exceptions)
