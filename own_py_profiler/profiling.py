# coding=utf-8
import datetime
import operator
import sys
from threading import local

import os

from .settings import SETTINGS

_thread_locals = local()

stacks = []

current_path = os.path.abspath(os.path.join(__file__, os.path.pardir))


class FrameNode(object):
    """ function node
    """

    fn_map = {
        # id(fn): [fn, call_times]
        0: [None, 1],
    }

    @classmethod
    def register_frame(cls, frame):
        frame_info = cls.fn_map.setdefault(id(frame), [frame, 0])
        frame_info[1] += 1
        cls.fn_map[id(frame)] = frame_info
        return frame_info

    def __init__(self, frame, children=None, cost=0):
        if frame is not None:
            frame_info = self.register_frame(frame)
            self.id = str(id(frame)) + ':' + str(frame_info[1])
            self.name = frame.f_code.co_name
        else:
            self.name = 'root'
            self.id = 0
        self.children = children or []
        self.cost = cost
        self.frame = frame

        self.start = None
        self.end = None

    @classmethod
    def root(cls):
        return cls(None)

    def is_root(self):
        return self.id == 0

    def __repr__(self):
        return self.name + ':' + str(self.cost)

    __str__ = __repr__

    def __eq__(self, other):
        return self.frame is other.frame


def _get_stack():
    """ get current thread user defined call stack.
    """
    if not hasattr(_thread_locals, 'cur_stack'):
        new_stack = [FrameNode.root()]
        stacks.append(new_stack)
        _thread_locals.cur_stack = new_stack
    return _thread_locals.cur_stack


def profiler(frame, event, func):
    """ profile the func 
    """
    frame_filename = frame.f_code.co_filename
    if (not frame_filename.startswith(SETTINGS['ROOT_DIR']) or frame_filename.startswith(current_path)):
        return
    stack = _get_stack()
    if event in ('call', ):
        node = FrameNode(frame)
        parent = stack[-1]
        parent.children.append(node)
        stack.append(node)
        node.start = datetime.datetime.now()

    elif event in ('return', ) and len(stack) > 1:
        node = stack.pop()
        node.end = datetime.datetime.now()
        time_cost = node.end - node.start
        node.cost = time_cost.total_seconds()
    else:  # event in ('c_call', 'c_return', 'exception', 'c_exception')
        pass


def _show_timing_cost(node, deep=None, parent_cost=0):
    if node.is_root():
        node.cost = sum([_.cost for _ in node.children])
    # calculate cost percent of parent
    cost_percent = ''
    if parent_cost:
        cost_percent = str(round((node.cost * 100.0) / parent_cost, 2)) + '%'

    deep = deep or []

    ver_con = '│   '
    ver_des = '    '
    tab_option = [ver_con, ver_des]
    child_con = '├───'
    child_des = '└───'

    filename = ''
    lineno = ''
    if node.frame:
        filename = node.frame.f_code.co_filename
        lineno = node.frame.f_code.co_firstlineno
    print ('%(name)-25s: %(cost_percent)5s %(cost)8s(S) file: %(file)s:%(lineno)s' 
           % dict(name=node.name, cost_percent=cost_percent, cost=node.cost, file=filename, lineno=lineno))
    cur_children = sorted(node.children, key=operator.attrgetter('cost'), reverse=True)
    max_index = len(cur_children) - 1
    for i, c in enumerate(cur_children):
        done = i == max_index
        start_char = child_des if done else child_con
        print ''.join([tab_option[_] for _ in deep]) + start_char,
        _show_timing_cost(c, deep=deep + [done], parent_cost=node.cost)


def show_timing_cost():
    for stack in stacks:
        _show_timing_cost(stack[0])


def start_profiling(root_dir='.'):
    ROOT_DIR = os.path.abspath(root_dir)
    SETTINGS['ROOT_DIR'] = ROOT_DIR
    sys.setprofile(profiler)


class Profiling:
    """ Profile context manager
    """

    def __init__(self, path='.'):
        self.path = path

    def __enter__(self):
        start_profiling(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.setprofile(None)
        show_timing_cost()
