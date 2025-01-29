from dataclasses import dataclass, field
from typing import List

from specklepy.objects.base import Base
from specklepy.objects.geometry.line import Line
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.polyline import Polyline
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Polycurve(
    Base, IHasUnits, ICurve, IHasArea, speckle_type="Objects.Geometry.Polycurve"
):
    """
    a curve that is comprised of multiple curves connected
    """

    segments: List[ICurve] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"segments: {len(self.segments)}, "
            f"closed: {self.is_closed()}, "
            f"units: {self.units})"
        )

    def is_closed(self, tolerance: float = 1e-6) -> bool:
        """
        checks if the polycurve is closed
        (comparing start of first segment to end of last segment)
        """
        if len(self.segments) < 1:
            return False

        first_segment = self.segments[0]
        last_segment = self.segments[-1]

        if not (hasattr(first_segment, "start") and hasattr(last_segment, "end")):
            return False

        start_pt = first_segment.start
        end_pt = last_segment.end

        if not (isinstance(start_pt, Point) and isinstance(end_pt, Point)):
            return False

        return start_pt.distance_to(end_pt) <= tolerance

    @property
    def length(self) -> float:
        return self.__dict__.get("_length", 0.0)

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__["_length"] = value

    def calculate_length(self) -> float:
        """
        calculate total length of all segments
        """
        total_length = 0.0
        for segment in self.segments:
            if hasattr(segment, "length"):
                total_length += segment.length
        return total_length

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value

    @classmethod
    def from_polyline(cls, polyline: Polyline) -> "Polycurve":
        """
        constructs a new polycurve instance from an existing polyline curve
        """
        polycurve = cls(units=polyline.units)
        points = polyline.get_points()
        for i in range(len(points) - 1):
            line = Line(start=points[i], end=points[i + 1], units=polyline.units)
            polycurve.segments.append(line)

        if polyline.is_closed():
            line = Line(start=points[-1], end=points[0], units=polyline.units)
            polycurve.segments.append(line)

        if hasattr(polyline, "_length"):
            polycurve.length = polyline.length
        if hasattr(polyline, "_area"):
            polycurve.area = polyline.area

        return polycurve
