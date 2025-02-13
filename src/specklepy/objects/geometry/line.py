from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits


@dataclass(kw_only=True)
class Line(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Line"):
    start: Point
    end: Point

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)
