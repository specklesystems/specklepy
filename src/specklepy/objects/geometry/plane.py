from dataclasses import dataclass
from typing import List, Tuple

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.interfaces import IHasUnits, ITransformable
from specklepy.objects.models.units import (
    get_encoding_from_units,
    get_units_from_encoding
)


@dataclass(kw_only=True)
class Plane(Base, ITransformable, IHasUnits, speckle_type="Objects.Geometry.Plane"):
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

    def to_list(self) -> List[float]:
        """
        returns the values of this Plane as a list of numbers
        """
        result = []
        result.extend(self.origin.to_list())
        result.extend(self.normal.to_list())
        result.extend(self.xdir.to_list())
        result.extend(self.ydir.to_list())
        result.append(get_encoding_from_units(self.units))
        return result

    @classmethod
    def from_list(cls, coords: List[float]) -> "Plane":
        """
        creates a new Plane based on a list of values
        """
        units = get_units_from_encoding(int(coords[-1]))

        plane = cls(
            origin=Point(x=coords[0], y=coords[1], z=coords[2], units=units),
            normal=Vector(x=coords[3], y=coords[4], z=coords[5], units=units),
            xdir=Vector(x=coords[6], y=coords[7], z=coords[8], units=units),
            ydir=Vector(x=coords[9], y=coords[10], z=coords[11], units=units),
            units=units,
        )

        return plane

    def transform_to(self, transform) -> Tuple[bool, Base]:
        """
        transform this plane using the given transform
        """
        _, transformed_origin = self.origin.transform_to(transform)
        _, transformed_normal = self.normal.transform_to(transform)
        _, transformed_xdir = self.xdir.transform_to(transform)
        _, transformed_ydir = self.ydir.transform_to(transform)

        transformed = Plane(
            origin=transformed_origin,
            normal=transformed_normal,
            xdir=transformed_xdir,
            ydir=transformed_ydir,
            applicationId=self.applicationId,
            units=self.units,
        )

        return True, transformed
