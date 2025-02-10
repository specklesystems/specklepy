from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class Vector(
    Base, IHasUnits, speckle_type="Objects.Geometry.Vector", serialize_ignore={"length"}
):
    """
    a 3-dimensional vector
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"x: {self.x}, "
            f"y: {self.y}, "
            f"z: {self.z}, "
            f"units: {self.units})"
        )

    @property
    def length(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5
