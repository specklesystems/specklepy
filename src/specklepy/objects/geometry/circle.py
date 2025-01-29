import math
from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Circle(Base, IHasUnits, ICurve, IHasArea, speckle_type="Objects.Geometry.Circle"):
    """
    a circular curve based on a plane
    """

    plane: Plane
    center: Point
    radius: float

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"plane: {self.plane}, "
            f"center: {self.center}, "
            f"radius: {self.radius}, "
            f"units: {self.units})"
        )

    @property
    def length(self) -> float:
        return 2 * math.pi * self.radius

    @property
    def area(self) -> float:
        return math.pi * self.radius**2
