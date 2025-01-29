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
        return (
            f"{self.__class__.__name__}("
            f"x: {self.x}, "
            f"y: {self.y}, "
            f"z: {self.z}, "
            f"weight: {self.weight}, "
            f"units: {self.units})"
        )
