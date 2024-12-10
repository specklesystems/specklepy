from abc import ABCMeta, abstractmethod
from specklepy.objects_v3.models.base import Base
from specklepy.objects.primitive import Interval


# generic interfaces
class ICurve(Base, speckle_type="ICurve", metaclass=ABCMeta):
    @property
    @abstractmethod
    def length(self) -> float:
        pass

    @property
    @abstractmethod
    def domain(self) -> Interval:
        pass

    @property
    @abstractmethod
    def units(self) -> str:
        pass


class IDisplayValue(Base, speckle_type="IDisplayValue", metaclass=ABCMeta):
    @property
    @abstractmethod
    def display_value(self):
        pass


# data object interfaces
class IProperties(Base, speckle_type="IProperties", metaclass=ABCMeta):
    @property
    @abstractmethod
    def properties(self) -> dict[str, object]:
        pass


class IDataObject(IProperties, IDisplayValue[list[Base]], speckle_type="IDataObject"):
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class IBlenderObject(IDataObject, speckle_type="IBlenderObject"):
    @property
    @abstractmethod
    def type(self) -> str:
        pass
