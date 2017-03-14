# OwnPyProfiler
A profiler only profile the code you specify.

# Usage

``` python
from own_py_profiler import Profiling

with Profiling('..'):  # the param is the path of codes you want to profile.
    my_function()
```

Also can find demo in [test.test_timing](https://github.com/weidwonder/OwnPyProfiler/blob/master/test/test_timing.py)
