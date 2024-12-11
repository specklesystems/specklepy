from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from specklepy.objects_v3.models.base import Base
from specklepy.objects.primitive import Interval
from specklepy.objects_v3.models.units import Units
from specklepy.logging.exceptions import SpeckleInvalidUnitException
from typing import TypeVar, Generic

T = TypeVar('T')  # define type variable for generic type


# generic interfaces
class ICurve(metaclass=ABCMeta):
    @property
    @abstractmethod
    def length(self) -> float:
        pass

    @property
    @abstractmethod
    def _domain(self) -> Interval:
        pass

    @property
    @abstractmethod
    def units(self) -> str:
        pass


class IDisplayValue(Generic[T], metaclass=ABCMeta):
    @property
    @abstractmethod
    def display_value(self) -> T:
        pass


class IHasUnits(metaclass=ABCMeta):
    """Interface for objects that have units."""

    _units: str | None = None

    @property
    def units(self) -> str | None:
        """Get the units of the object"""
        return self._units

    @units.setter
    def units(self, value: str | Units | None):
        """
        While this property accepts any string value, geometry expects units 
        to be specific strings (see Units enum)
        """
        if isinstance(value, str) or value is None:
            self._units = value
        elif isinstance(value, Units):
            self._units = value.value
        else:
            raise SpeckleInvalidUnitException(
                f"Unknown type {type(value)} received for units"
            )


# data object interfaces
class IProperties(metaclass=ABCMeta):
    @property
    @abstractmethod
    def properties(self) -> dict[str, object]:
        pass


class IDataObject(IProperties, IDisplayValue[list[Base]], metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class IBlenderObject(IDataObject, metaclass=ABCMeta):
    @property
    @abstractmethod
    def type(self) -> str:
        pass
