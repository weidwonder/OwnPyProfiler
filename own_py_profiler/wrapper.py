# coding=utf-8
import datetime
from functools import wraps
from threading import local

from .settings import SETTINGS

_thread_locals = local()

stacks = []


class FuncNode(object):
    """ function node
    """

    fn_map = {
        # id(fn): [fn, call_times]
        0: [None, 1],
    }

    @classmethod
    def register_fn(cls, fn):
        fn_info = cls.fn_map.setdefault(id(fn), [fn, 0])
        fn_info[1] += 1
        cls.fn_map[id(fn)] = fn_info
        return fn_info

    def __init__(self, fn, children=None, cost=0):
        if fn is not None:
            fn_info = self.register_fn(fn)
            self.id = str(id(fn)) + ':' + str(fn_info[1])
        else:
            self.id = 0
        self.children = children or []
        self.cost = cost
        self.fn = fn

    @classmethod
    def root(cls):
        return cls(None)

    def is_root(self):
        return self.id == 0

    def __repr__(self):
        if self.fn is None:
            return 'root' + ':' + str(self.cost)
        return self.fn.__name__ + ':' + str(self.cost)

    __str__ = __repr__

    def __eq__(self, other):
        return self.fn == other.fn


def _get_stack():
    """ get current thread user defined call stack.
    """
    if not hasattr(_thread_locals, 'cur_stack'):
        new_stack = [FuncNode.root()]
        stacks.append(new_stack)
        _thread_locals.cur_stack = new_stack
    return _thread_locals.cur_stack


def timing(func):
    """ wrap func to record time cost.
    """
    @wraps(func)
    def wrap_func(*args, **kws):
        if not SETTINGS['TIMING_STARTED']:
            return func(*args, **kws)
        stack = _get_stack()
        node = FuncNode(func)
        parent = stack[-1]
        parent.children.append(node)
        stack.append(node)

        start = datetime.datetime.now()
        rtn = func(*args, **kws)
        end = datetime.datetime.now()

        stack.pop()
        time_cost = end - start
        node.cost = time_cost.total_seconds()
        return rtn

    return wrap_func
