import math
from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits


@dataclass(kw_only=True)
class Arc(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Arc", serialize_ignore={"radius", "length"}):
    plane: Plane
    startPoint: Point
    midPoint: Point
    endPoint: Point

    @property
    def radius(self) -> float:
        return self.__dict__.get('_radius')

    @radius.setter
    def radius(self, value: float) -> None:
        self.__dict__['_radius'] = value

    @property
    def length(self) -> float:
        return self.__dict__.get('_length')

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__['_length'] = value

    def calculate_radius(self) -> float:
        return self.startPoint.distance_to(self.plane.origin)

    def calculate_length(self) -> float:
        start_to_mid = self.startPoint.distance_to(self.midPoint)
        mid_to_end = self.midPoint.distance_to(self.endPoint)
        r = self.calculate_radius()
        angle = (2 * math.asin(start_to_mid / (2 * r))) + \
            (2 * math.asin(mid_to_end / (2 * r)))
        return r * angle
