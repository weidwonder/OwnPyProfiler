# coding=utf-8
import operator
import sys

import os

from .importer import _wrap_timing, ProfilingImporter
from .wrapper import stacks
from settings import SETTINGS


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

    filename = node.fn.__code__.co_filename if node.fn else ''
    print '%(name)-25s: %(cost_percent)5s %(cost)8s(S) file: %(file)s' % dict(name=getattr(node.fn, '__name__', 'root'),
                                                                              cost_percent=cost_percent, cost=node.cost,
                                                                              file=filename)
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


def install_importer(root_dir='.'):
    ROOT_DIR = os.path.abspath(root_dir)
    SETTINGS['ROOT_DIR'] = ROOT_DIR
    importer = ProfilingImporter()
    sys.meta_path = [importer]


def activate_timing(_locals):
    for name, attr in _locals.items():
        if hasattr(attr, '__module__'):
            if attr.__module__ == '__main__':
                new_attr, to_set = _wrap_timing(attr)
                if to_set:
                    _locals[name] = new_attr
    SETTINGS['TIMING_STARTED'] = True
