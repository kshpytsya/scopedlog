from . import ScopedLogIdGenerator
import uuid as _uuid


class Uuid1ScopeIdGenerator(ScopedLogIdGenerator):
    def __call__(self, scope_name):
        return str(_uuid.uuid1())


class Uuid4ScopeIdGenerator(ScopedLogIdGenerator):
    def __call__(self, scope_name):
        return str(_uuid.uuid4())
