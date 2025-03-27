from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Spiral(Base, IHasUnits, ICurve, IHasArea, speckle_type="Objects.Geometry.Spiral"):
    """
    a spiral
    """

    start_point: Point
    end_point: Point
    plane: Plane  # plane with origin at spiral center
    turns: float  # total angle of spiral.
    pitch: float
    pitch_axis: Vector

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"start_point: {self.start_point}, "
            f"end_point: {self.end_point}, "
            f"plane: {self.plane}, "
            f"turns: {self.turns}, "
            f"pitch: {self.pitch}, "
            f"pitch_axis: {self.pitch_axis}, "
            f"units: {self.units})"
        )

    @property
    def length(self) -> float:
        return self.__dict__.get("_length", 0.0)

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__["_length"] = value

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value
