from dataclasses import dataclass, field

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Line(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Line"):
    """
    a line defined by two points in 3D space
    """

    start: Point
    end: Point

    @property
    def length(self) -> float:
        """
        calculate the length of the line using Point's distance_to method
        """
        return self.start.distance_to(self.end)
