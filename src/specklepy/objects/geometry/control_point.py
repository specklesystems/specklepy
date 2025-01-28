from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class ControlPoint(Base, IHasUnits, speckle_type="Objects.Geometry.ControlPoint"):
    """
    a single 3-dimensional point
    """
    x: float
    y: float
    z: float
    weight: float

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, weight: {self.weight}, units: {self.units})"
