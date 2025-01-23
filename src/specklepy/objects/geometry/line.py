from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits


@dataclass(kw_only=True)
class Line(
    Base,
    IHasUnits,
    ICurve,
    speckle_type="Objects.Geometry.Line",
    serialize_ignore={"length"}
):
    start: Point
    end: Point

    @property
    def length(self) -> float:
        return self.__dict__.get('_length')

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__['_length'] = value

    def calculate_length(self) -> float:
        return self.start.distance_to(self.end)
