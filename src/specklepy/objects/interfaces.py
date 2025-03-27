from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Generic, List, TypeVar

from specklepy.logging.exceptions import SpeckleInvalidUnitException
from specklepy.objects.base import Base
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval

T = TypeVar("T")  # define type variable for generic type


# generic interfaces
@dataclass(kw_only=True)
class ICurve(metaclass=ABCMeta):
    _domain: Interval = field(default_factory=Interval.unit_interval, init=False)

    @property
    @abstractmethod
    def length(self) -> float:
        pass

    @property
    def domain(self) -> Interval:
        return self._domain

    @domain.setter
    def domain(self, value: Interval) -> None:
        if not isinstance(value, Interval):
            raise TypeError(f"Domain must be an Interval, got {type(value)}")
        self._domain = value


class IDisplayValue(Generic[T], metaclass=ABCMeta):
    @property
    @abstractmethod
    def displayValue(self) -> T:
        pass


# field interfaces
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
    _area: float = field(init=False, repr=False)

    @property
    @abstractmethod
    def area(self) -> float:
        pass

    @area.setter
    def area(self, value: float):
        if not isinstance(value, int | float):
            raise ValueError(f"Area must be a number, got {type(value)}")
        self._area = float(value)


@dataclass(kw_only=True)
class IHasVolume(metaclass=ABCMeta):
    _volume: float = field(init=False, repr=False)

    @property
    @abstractmethod
    def volume(self) -> float:
        pass

    @volume.setter
    def volume(self, value: float):
        if not isinstance(value, int | float):
            raise ValueError(f"Volume must be a number, got {type(value)}")
        self._volume = float(value)


# data object interfaces
class IProperties(metaclass=ABCMeta):
    @property
    @abstractmethod
    def properties(self) -> Dict[str, object]:
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


class IGisObject(IDataObject, metaclass=ABCMeta):
    @property
    @abstractmethod
    def type(self) -> str:
        pass
