from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class Point(Base, IHasUnits, speckle_type="Objects.Geometry.Point"):
    """
    a 3-dimensional point
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

    def distance_to(self, other: "Point") -> float:
        """
        calculates the distance between this point and another given point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"Expected Point object, got {type(other)}")

        # we assume that host application units are the same for both points
        # unit conversion could be expensive, so we avoid it here
        dx = other.x - self.x
        dy = other.y - self.y
        dz = other.z - self.z

        return (dx * dx + dy * dy + dz * dz) ** 0.5
