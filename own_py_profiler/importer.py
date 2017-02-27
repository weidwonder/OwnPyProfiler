import imp
import inspect

from .settings import SETTINGS
from .wrapper import timing


class ProfilingImporter:
    """ Importer
    """

    def __init__(self):
        if not SETTINGS['ROOT_DIR']:
            raise RuntimeError(u'Please use `install_importer` to install ProfilingImporter')

    def find_module(self, fullname, path=None):
        # Note: we ignore 'path' argument since it is only used via meta_path
        subname = fullname.split(".")[-1]
        if subname != fullname and path is None:
            return None
        try:
            file, filename, etc = imp.find_module(subname, path)
        except ImportError:
            return None
        return ProfilingLoader(fullname, file, filename, etc)


class ProfilingLoader:
    """ ImpLoader
    """
    code = source = None

    def __init__(self, fullname, file, filename, etc):
        self.file = file
        self.filename = filename
        self.fullname = fullname
        self.etc = etc

    def load_module(self, fullname):
        self._reopen()
        try:
            mod = imp.load_module(fullname, self.file, self.filename, self.etc)
        finally:
            if self.file:
                self.file.close()
        # Note: we don't set __loader__ because we want the module to look
        # normal; i.e. this is just a wrapper for standard import machinery
        self.inject_timing(mod)
        return mod

    def get_data(self, pathname):
        return open(pathname, "rb").read()

    def _reopen(self):
        if self.file and self.file.closed:
            mod_type = self.etc[2]
            if mod_type == imp.PY_SOURCE:
                self.file = open(self.filename, 'rU')
            elif mod_type in (imp.PY_COMPILED, imp.C_EXTENSION):
                self.file = open(self.filename, 'rb')

    def inject_timing(self, mod):
        if self.filename.startswith(SETTINGS['ROOT_DIR']) and self.filename != __file__:
            for attr in dir(mod):
                if not attr.startswith('__'):
                    real_attr = getattr(mod, attr)
                    attr_module = getattr(real_attr, '__module__', None)
                    if attr_module == self.fullname:
                        new_attr, to_set = _wrap_timing(real_attr)
                        if to_set:
                            setattr(mod, attr, new_attr)


class VariableTypes:
    FREE = 1
    IN_CLASS = 2


silence_attrs = {'__class__', '__new__'}


def _wrap_timing(obj, _type=VariableTypes.FREE):
    if inspect.isclass(obj):
        for attr in dir(obj):
            if attr in silence_attrs: continue
            try:
                new_attr, to_set = _wrap_timing(getattr(obj, attr), _type=VariableTypes.IN_CLASS)
                if to_set:
                    setattr(obj, attr, new_attr)
            except:
                pass
        return obj, False
    if (inspect.ismethod(obj) and obj.__func__.__code__.co_filename.startswith(SETTINGS['ROOT_DIR'])):
        if obj.__self__ is not None:
            # obj is a classmethod
            if _type is VariableTypes.IN_CLASS:
                # obj is a reference to a class method
                return classmethod(obj.__func__), True
            else:
                return obj, False
        else:
            # obj is a instance method
            return timing(obj), True
    if inspect.isfunction(obj) and obj.__code__.co_filename.startswith(SETTINGS['ROOT_DIR']):
        if _type is VariableTypes.IN_CLASS:
            # obj is a staticmethod
            return staticmethod(obj.__func__), True
        else:
            # obj is a free function
            return timing(obj), True
    return obj, False
