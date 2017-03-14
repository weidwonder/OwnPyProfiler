import inspect
from functools import partial, wraps

from django.conf import settings
from django.views import View

from own_py_profiler import Profiling

BASE_DIR = settings.BASE_DIR


def _view_wrap(path, view):
    if issubclass(view, View):
        view_dispatch = view.dispatch

        @wraps(view_dispatch)
        def new_dispatch(*args, **kws):
            with Profiling(path):
                return view_dispatch(*args, **kws)

        view.dispatch = new_dispatch
        return view
    elif inspect.isfunction(view):
        @wraps(view)
        def new_view(*args, **kws):
            with Profiling(path):
                return view(*args, **kws)

        return new_view
    else:
        raise TypeError('The object `view_profiling` wraps must be a View class or a function not %r' % view)


def view_profiling(view_or_path):
    """ django view profiling 
    """
    if isinstance(view_or_path, basestring):
        path = view_or_path
        return partial(_view_wrap, path)
    else:
        return _view_wrap(BASE_DIR, view_or_path)
