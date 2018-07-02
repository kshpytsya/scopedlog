from . import ScopedLogSink


class StructlogSink(ScopedLogSink):
    def __init__(
        self,
        log
    ):
        self._log = log

    def log_debug(self, scope_name, state_kw):
        self._log.debug(scope_name, **state_kw)

    def log_info(self, scope_name, state_kw):
        self._log.info(scope_name, **state_kw)

    def log_warn(self, scope_name, state_kw):
        self._log.warn(scope_name, **state_kw)

    def log_error(self, scope_name, state_kw):
        self._log.error(scope_name, **state_kw)

    def log_exception(self, scope_name, state_kw):
        state_kw["exc_info"] = state_kw.pop("scope_exception")
        self._log.error(scope_name, **state_kw)
