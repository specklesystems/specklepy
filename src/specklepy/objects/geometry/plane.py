from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class Plane(Base, IHasUnits, speckle_type="Objects.Geometry.Plane"):
    """
    a plane consisting of an origin Point, and 3 Vectors as its X, Y and Z axis.
    """

    origin: Point
    normal: Vector
    xdir: Vector
    ydir: Vector

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"origin: {self.origin}, "
            f"normal: {self.normal}, "
            f"xdir: {self.xdir}, "
            f"ydir: {self.ydir}, "
            f"units: {self.units})"
        )
