from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.interfaces import IHasArea, IHasUnits, ICurve


@dataclass(kw_only=True)
class Spiral(Base, IHasUnits, ICurve, IHasArea, speckle_type="Objects.Geometry.Spiral"):
    """
    a spiral
    """

    start_point: Point
    end_point: Point
    plane: Plane  # plane with origin at spiral center
    turns: float  # total angle of spiral. positive is counter-clockwise, negative is clockwise
    pitch: float
    pitch_axis: Vector

    @property
    def length(self) -> float:
        return self.__dict__.get('_length', 0.0)

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__['_length'] = value

    @property
    def area(self) -> float:
        return self.__dict__.get('_area', 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__['_area'] = value
