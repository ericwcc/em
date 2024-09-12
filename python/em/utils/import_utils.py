from typing import Optional, Type, Any
from importlib import import_module

def load_class(path: str, base_klass: Type = None) -> Type:
    klass = import_string(path)
    if klass is base_klass or not issubclass(klass, base_klass):
        raise Exception(f'Class {path} must implement {base_klass}')
    return klass

def load_function(path: str):
    function = import_string(path)
    if not callable(function):
        raise Exception(f'{path} is not a valid function')
    return function

def import_string(path: str) -> Any:
    module_path, _, attr_name = path.rpartition('.')
    module = import_module(module_path)
    return getattr(module, attr_name)