from dataclasses import dataclass
from specklepy.objects_v3.models.base import Base
from specklepy.objects_v3.primitive import Interval
from specklepy.objects_v3.interfaces import ICurve


@dataclass(kw_only=True)
class Point(Base, speckle_type="Objects.Geometry.Point"):
    """
    a 3-dimensional point
    """
    x: float
    y: float
    z: float
    units: str

    def __init__(self, x: float, y: float, z: float, units: str, applicationId: str | None = None) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.units = units
        self.applicationId = applicationId

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_list(cls, coords: list[float], units: str) -> 'Point':
        return cls(coords[0], coords[1], coords[2], units)

    @classmethod
    def from_coords(cls, x: float, y: float, z: float, units: str) -> 'Point':
        return cls(x, y, z, units)


@dataclass(kw_only=True)
class Line(Base, ICurve, speckle_type="Objects.Geometry.Line"):
    """
    a line defined by two points in 3D space
    """
    start: Point
    end: Point
    units: str
    domain: Interval = Interval.unit_interval()

    def __init__(
        self,
        start: Point,
        end: Point,
        units: str,
        domain: Interval | None = None,
        applicationId: str | None = None
    ) -> None:
        super().__init__()
        self.start = start
        self.end = end
        self.units = units
        self.domain = domain or Interval.unit_interval()
        self.applicationId = applicationId

    @property
    def length(self) -> float:
        return Point.distance(self.start, self.end)

    def to_list(self) -> list[float]:
        result = []
        result.extend(self.start.to_list())
        result.extend(self.end.to_list())
        result.extend([self.domain.start, self.domain.end])
        return result

    @classmethod
    def from_list(cls, coords: list[float], units: str) -> 'Line':
        if len(coords) < 6:
            raise ValueError(
                "Line from coordinate array requires 6 coordinates.")

        start = Point(coords[0], coords[1], coords[2], units)
        end = Point(coords[3], coords[4], coords[5], units)

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
        start = Point(start_x, start_y, start_z, units)
        end = Point(end_x, end_y, end_z, units)
        return cls(start=start, end=end, units=units)
