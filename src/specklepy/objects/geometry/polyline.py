from dataclasses import dataclass
from typing import List

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits
from specklepy.objects.models.units import Units


@dataclass(kw_only=True)
class Polyline(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Polyline"):
    """
    a polyline curve, defined by a set of vertices.
    """

    value: List[float]
    closed: bool = False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"value: {self.value}, "
            f"closed: {self.closed}, "
            f"units: {self.units})"
        )

    @staticmethod
    def is_closed(points: List[float], tolerance: float = 1e-6) -> bool:
        """
        check if the polyline is closed
        """
        if len(points) < 6:  # need at least 2 points to be closed
            return False

        # compare first and last points
        start = Point(x=points[0], y=points[1], z=points[2], units=Units.m)
        end = Point(x=points[-3], y=points[-2], z=points[-1], units=Units.m)

        return start.distance_to(end) <= tolerance

    @property
    def length(self) -> float:
        return self.__dict__.get("_length", 0.0)

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__["_length"] = value

    def calculate_length(self) -> float:
        points = self.get_points()
        total_length = 0.0
        for i in range(len(points) - 1):
            total_length += points[i].distance_to(points[i + 1])
        if self.closed and points:
            total_length += points[-1].distance_to(points[0])
        return total_length

    def get_points(self) -> List[Point]:
        """
        converts the raw coordinate list into Point objects
        """
        if len(self.value) % 3 != 0:
            raise ValueError(
                "Polyline value list is malformed: expected length to be multiple of 3"
            )

        points = []
        for i in range(0, len(self.value), 3):
            point = Point(
                x=self.value[i],
                y=self.value[i + 1],
                z=self.value[i + 2],
                units=self.units,
            )
            points.append(point)
        return points
