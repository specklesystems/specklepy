import sys
import pkgutil
from pathlib import Path
from importlib import import_module
from inspect import isclass, getmembers

# TODO: get classes to show up in intellisense!
for (_, name, _) in pkgutil.iter_modules([Path(__file__).parent]):

    imported_module = import_module(f".{name}", package=__name__)

    for attr_name, attr in getmembers(imported_module):
        if isclass(attr):
            setattr(sys.modules[__name__], attr_name, attr)
