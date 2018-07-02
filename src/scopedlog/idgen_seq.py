from . import ScopedLogIdGenerator
import threading as _threading


class _GlobalCounter:
    def __init__(self):
        self._lock = _threading.Lock()
        self._value = 0

    def new_value(self):
        with self._lock:
            self._value += 1
            return self._value


class GlobalSeqScopeIdGenenerator(ScopedLogIdGenerator):
    _counter = _GlobalCounter()

    def __call__(self, scope_name):
        return GlobalSeqScopeIdGenenerator._counter.new_value()


class _CounterDict:
    def __init__(self):
        self._lock = _threading.Lock()
        self._counters = dict()

    def new_value(self, key):
        with self._lock:
            v = self._counters.get(key, 0) + 1
            self._counters[key] = v
            return v


class SeqScopeIdGenenerator(ScopedLogIdGenerator):
    _counters = _CounterDict()

    def __call__(self, scope_name):
        return SeqScopeIdGenenerator._counters.new_value(scope_name)
