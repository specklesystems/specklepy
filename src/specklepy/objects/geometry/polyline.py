from dataclasses import dataclass, field
from typing import List, Tuple

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits, ITransformable
from specklepy.objects.models.units import (
    Units,
    get_encoding_from_units
)
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Polyline(Base, IHasUnits, ICurve, ITransformable, speckle_type="Objects.Geometry.Polyline"):
    """
    a polyline curve, defined by a set of vertices.
    """

    value: List[float]
    closed: bool = False
    domain: Interval = field(default_factory=Interval.unit_interval)

    @property
    def length(self) -> float:
        points = self.get_points()
        total_length = 0.0
        for i in range(len(points) - 1):
            total_length += points[i].distance_to(points[i + 1])
        if self.closed and points:
            total_length += points[-1].distance_to(points[0])
        return total_length

    @property
    def _domain(self) -> Interval:
        """
        internal domain property for ICurve interface
        """
        return self.domain

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
            points.append(
                Point(
                    x=self.value[i],
                    y=self.value[i + 1],
                    z=self.value[i + 2],
                    units=self.units,
                )
            )
        return points

    def to_list(self) -> List[float]:
        """
        returns the values of this Polyline as a list of numbers
        """
        result = []
        result.append(len(self.value) + 6)  # total list length
        # type indicator for polyline ?? not sure about this
        result.append("Objects.Geometry.Polyline")
        result.append(1 if self.closed else 0)
        result.append(self.domain.start)
        result.append(self.domain.end)
        result.append(len(self.value))
        result.extend(self.value)
        result.append(get_encoding_from_units(self.units))
        return result

    @classmethod
    def from_list(cls, coords: List[float], units: str | Units) -> "Polyline":
        """
        creates a new Polyline based on a list of coordinates
        """
        point_count = int(coords[5])
        return cls(
            closed=(int(coords[2]) == 1),
            domain=Interval(start=coords[3], end=coords[4]),
            value=coords[6: 6 + point_count],
            units=units,
        )

    def transform_to(self, transform) -> Tuple[bool, "Polyline"]:
        """
        transform this polyline by transforming all its vertices
        """
        if len(self.value) % 3 != 0:
            return False, self

        # Transform each point in the value list
        transformed_values = []
        for i in range(0, len(self.value), 3):
            point = Point(
                x=self.value[i],
                y=self.value[i + 1],
                z=self.value[i + 2],
                units=self.units
            )
            success, transformed_point = point.transform_to(transform)
            if not success:
                return False, self

            transformed_values.extend([
                transformed_point.x,
                transformed_point.y,
                transformed_point.z
            ])

        transformed = Polyline(
            value=transformed_values,
            closed=self.closed,
            domain=self.domain,
            units=self.units,
            applicationId=self.applicationId
        )
        return True, transformed
