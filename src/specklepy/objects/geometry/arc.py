from dataclasses import dataclass, field
from typing import List, Tuple
import math

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.interfaces import ICurve, IHasUnits, ITransformable
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Arc(Base, IHasUnits, ICurve, ITransformable, speckle_type="Objects.Geometry.Arc"):

    plane: Plane
    startPoint: Point
    midPoint: Point
    endPoint: Point
    domain: Interval = field(default_factory=Interval.unit_interval)

    @property
    def radius(self) -> float:
        return self.startPoint.distance_to(self.plane.origin)

    @property
    def measure(self) -> float:
        start_to_mid = self.startPoint.distance_to(self.midPoint)
        mid_to_end = self.midPoint.distance_to(self.endPoint)
        r = self.radius
        return (2 * math.asin(start_to_mid / (2 * r))) + (2 * math.asin(mid_to_end / (2 * r)))

    @property
    def length(self) -> float:
        return self.radius * self.measure

    @property
    def _domain(self) -> Interval:
        return self.domain

    def transform_to(self, transform) -> Tuple[bool, "Arc"]:
        _, transformed_start = self.startPoint.transform_to(transform)
        _, transformed_mid = self.midPoint.transform_to(transform)
        _, transformed_end = self.endPoint.transform_to(transform)
        _, transformed_plane = self.plane.transform_to(transform)

        transformed = Arc(
            startPoint=transformed_start,
            endPoint=transformed_end,
            midPoint=transformed_mid,
            plane=transformed_plane,
            domain=self.domain,
            units=self.units,
            applicationId=self.applicationId
        )
        return True, transformed

    def to_list(self) -> List[float]:
        from specklepy.objects.models.units import get_encoding_from_units

        result = []
        result.append(self.radius)
        result.append(0)
        result.append(0)
        result.append(self.measure)
        result.append(self.domain.start)
        result.append(self.domain.end)
        result.extend(self.plane.to_list())
        result.extend(self.startPoint.to_list())
        result.extend(self.midPoint.to_list())
        result.extend(self.endPoint.to_list())
        result.append(get_encoding_from_units(self.units))

        result.insert(0, 1)
        result.insert(0, len(result))
        return result

    @classmethod
    def from_list(cls, coords: List[float]) -> "Arc":
        from specklepy.objects.models.units import get_units_from_encoding

        units = get_units_from_encoding(int(coords[-1]))

        arc = cls(
            domain=Interval(start=coords[6], end=coords[7]),
            units=units,
            plane=Plane.from_list(coords[8:21]),
            startPoint=Point.from_list(coords[21:24], units),
            midPoint=Point.from_list(coords[24:27], units),
            endPoint=Point.from_list(coords[27:30], units)
        )

        arc.plane.units = arc.units
        return arc
