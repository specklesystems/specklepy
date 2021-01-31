from pathlib import Path
import sys
import inspect
import pkgutil
from importlib import import_module
from .base import Base


for (_, name, _) in pkgutil.iter_modules([Path(__file__).parent]):
    imported_module = import_module("." + name, package=__name__)
    classes = inspect.getmembers(imported_module, inspect.isclass)
    for c in classes:
        if issubclass(c[1], Base):
            setattr(sys.modules[__name__], c[0], c[1])
