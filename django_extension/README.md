# OwnPyProfiler\-django
A view profiler only profile the code you specify.

# Usage

``` python
from OwnPyProfile.django_extension import view_profiling

@view_profiling
def your_view(some_params):
    pass

@view_profiling
class YourView(View):
    pass

# or you can specify the code path
@view_profiling('../..')
class YourView(View):
    pass
```
