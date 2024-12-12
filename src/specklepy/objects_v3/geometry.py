from dataclasses import dataclass, field
from specklepy.objects_v3.models.base import Base
from specklepy.objects_v3.primitive import Interval
from specklepy.objects_v3.models.units import Units
from specklepy.objects_v3.interfaces import ICurve, IHasUnits
from typing import List


@dataclass(kw_only=True)
class Point(Base, IHasUnits, speckle_type="Objects.Geometry.Point"):
    """
    a 3-dimensional point
    """
    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, units: {self.units})"

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_list(cls, coords: List[float], units: str | Units) -> 'Point':
        return cls(x=coords[0], y=coords[1], z=coords[2], units=units)

    @classmethod
    def from_coords(cls, x: float, y: float, z: float, units: str | Units) -> 'Point':
        return cls(x=x, y=y, z=z, units=units)

    def distance_to(self, other: 'Point') -> float:
        """
        calculates the distance between this point and another given point
        """
        dx = other.x - self.x
        dy = other.y - self.y
        dz = other.z - self.z
        return (dx * dx + dy * dy + dz * dz) ** 0.5


@dataclass(kw_only=True)
class Line(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Line"):
    """
    a line defined by two points in 3D space
    """
    start: Point
    end: Point
    domain: Interval = field(default_factory=Interval.unit_interval)

    @property
    def length(self) -> float:
        """
        calculate the length of the line using Point's distance_to method
        """
        return self.start.distance_to(self.end)

    @property
    def _domain(self) -> Interval:
        return self.domain

    def to_list(self) -> List[float]:
        result = []
        result.extend(self.start.to_list())
        result.extend(self.end.to_list())
        result.extend([self.domain.start, self.domain.end])
        return result

    @classmethod
    def from_list(cls, coords: List[float], units: str) -> 'Line':
        if len(coords) < 6:
            raise ValueError(
                "Line from coordinate array requires 6 coordinates.")

        start = Point(x=coords[0], y=coords[1], z=coords[2], units=units)
        end = Point(x=coords[3], y=coords[4], z=coords[5], units=units)

        return cls(start=start, end=end, units=units)

    @classmethod
    def from_coords(
        cls,
        start_x: float,
        start_y: float,
        start_z: float,
        end_x: float,
        end_y: float,
        end_z: float,
        units: str
    ) -> 'Line':
        start = Point(x=start_x, y=start_y, z=start_z, units=units)
        end = Point(x=end_x, y=end_y, z=end_z, units=units)
        return cls(start=start, end=end, units=units)
