[![linux test status](https://img.shields.io/travis/kshpytsya/scopedlog.svg?label=Linux)](https://travis-ci.org/kshpytsya/scopedlog)

# scopedlog
A library for scoped logging on top of [structlog](http://www.structlog.org) (or similar sinks), inspired by the idea of an apparently defunct [lithoxyl](https://github.com/mahmoud/lithoxyl). Note that I ([kshpytsya](https://github.com/kshpytsya)) have deliberatly not looked into actual lithoxyl's implementation to keep a fresh mind.

Here is an example:

```python
import contextlib                                                                                                                         import structlog
import structlog.stdlib
import structlog.dev
import structlog.processors
import scopedlog
import scopedlog.sink_structlog
import scopedlog.idgen_seq

structlog.configure(processors=[
    structlog.stdlib.add_log_level,
    structlog.processors.ExceptionPrettyPrinter(),
    structlog.dev.ConsoleRenderer()
])

slog = scopedlog.ScopedLog(
    sink=scopedlog.sink_structlog.StructlogSink(structlog.get_logger()),
    id_gen=scopedlog.idgen_seq.GlobalSeqScopeIdGenenerator()
)

with contextlib.suppress(RuntimeError):
    with slog.info("scope1", k1=1) as sl:
        sl.debug("state1", k2=2, k3=3)
        sl.info("state1", k4=4)
        sl.warn("state1", k5=5)
        raise RuntimeError("bad one")

with contextlib.suppress(RuntimeError):
    with slog.debug("scope2", k1=1) as sl:
        sl.debug("state1", k2=2, k3=3)
        sl.info("state1", k4=4)
        sl.warn("state1", k5=5)
        raise RuntimeError("bad too ;)")

with slog.debug("scope3") as sl:
    sl.fail()

with slog.debug("scope4") as sl:
    sl.exit_kw["k1"] = 1
```
And expected output:
![](https://scopedlog-screenshot.surge.sh/scopedlog-screenshot.png)

See [tests](tests) for more examples.
