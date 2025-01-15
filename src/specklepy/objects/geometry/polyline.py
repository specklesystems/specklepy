from dataclasses import dataclass, field
from typing import List, Tuple, Any

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

    def to_list(self) -> List[Any]:
        """
        returns a serializable list of format:
        [total_length, speckle_type, units_encoding,
         is_closed,
         domain_start, domain_end,
         coords_count,
         x1, y1, z1, x2, y2, z2, ...]
         """
        result = []
        result.append(1 if self.closed else 0)  # convert bool to int
        result.extend([self.domain.start, self.domain.end])
        result.append(len(self.value))  # number of coordinates
        result.extend(self.value)  # all vertex coordinates

        # add header information
        result.insert(0, get_encoding_from_units(self.units))
        result.insert(0, self.speckle_type)
        result.insert(0, len(result) + 1)
        return result

    @classmethod
    def from_list(cls, coords: List[Any], units: str | Units) -> "Polyline":
        """
        creates a Polyline from a list of format:
        [total_length, speckle_type, units_encoding,
         is_closed,
         domain_start, domain_end,
         coords_count,
         x1, y1, z1, x2, y2, z2, ...]
         """
        is_closed = bool(coords[3])
        domain = Interval(start=coords[4], end=coords[5])
        coords_count = int(coords[6])
        vertex_coords = coords[7:7 + coords_count]

        return cls(
            value=vertex_coords,
            closed=is_closed,
            domain=domain,
            units=units
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
