from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, List, TypeVar

from specklepy.logging.exceptions import SpeckleInvalidUnitException
from specklepy.objects.base import Base
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval

T = TypeVar("T")  # define type variable for generic type


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


@dataclass(kw_only=True)
class IHasUnits(metaclass=ABCMeta):

    units: str | Units
    _units: str = field(repr=False, init=False)

    @property
    def units(self) -> str:
        return self._units

    @units.setter
    def units(self, value: str | Units):
        if isinstance(value, str):
            self._units = value
        elif isinstance(value, Units):
            self._units = value.value
        else:
            raise SpeckleInvalidUnitException(
                f"Unknown type {type(value)} received for units"
            )


@dataclass(kw_only=True)
class IHasArea(metaclass=ABCMeta):

    area: float
    _area: float = field(init=False, repr=False)

    @property
    def area(self) -> float:
        return self._area

    @area.setter
    def area(self, value: float):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Area must be a number, got {type(value)}")
        self._area = float(value)


@dataclass(kw_only=True)
class IHasVolume(metaclass=ABCMeta):

    volume: float
    _volume: float = field(init=False, repr=False)

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Volume must be a number, got {type(value)}")
        self._volume = float(value)


# data object interfaces
class IProperties(metaclass=ABCMeta):
    @property
    @abstractmethod
    def properties(self) -> dict[str, object]:
        pass


class IDataObject(IProperties, IDisplayValue[List[Base]], metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class IBlenderObject(IDataObject, metaclass=ABCMeta):
    @property
    @abstractmethod
    def type(self) -> str:
        pass
