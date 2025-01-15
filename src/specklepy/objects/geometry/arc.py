from dataclasses import dataclass, field
from typing import List, Tuple, Any
import math

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.interfaces import ICurve, IHasUnits, ITransformable
from specklepy.objects.primitive import Interval
from specklepy.objects.models.units import (
    get_encoding_from_units,
    get_units_from_encoding
)


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

    def to_list(self) -> List[Any]:
        """
        returns a serializable list of format:
        [total_length, speckle_type, units_encoding,
         radius, measure,
         domain_start, domain_end,
         plane_origin_x, plane_origin_y, plane_origin_z,
         plane_normal_x, plane_normal_y, plane_normal_z,
         plane_xdir_x, plane_xdir_y, plane_xdir_z,
         plane_ydir_x, plane_ydir_y, plane_ydir_z,
         start_x, start_y, start_z,
         mid_x, mid_y, mid_z,
         end_x, end_y, end_z]
         """
        result = []
        result.extend([self.radius, self.measure])
        result.extend([self.domain.start, self.domain.end])
        # skip length, type, units from Plane
        result.extend(self.plane.to_list()[3:])
        # skip length, type, units from Point
        result.extend(self.startPoint.to_list()[3:])
        # skip length, type, units from Point
        result.extend(self.midPoint.to_list()[3:])
        # skip length, type, units from Point
        result.extend(self.endPoint.to_list()[3:])

        # add header information
        result.insert(0, get_encoding_from_units(self.units))
        result.insert(0, self.speckle_type)
        result.insert(0, len(result) + 1)
        return result

    @classmethod
    def from_list(cls, coords: List[Any]) -> "Arc":
        """
        creates an Arc from a list of format:
        [total_length, speckle_type, units_encoding,
         radius, measure,
         domain_start, domain_end,
         plane_origin_x, plane_origin_y, plane_origin_z,
         plane_normal_x, plane_normal_y, plane_normal_z,
         plane_xdir_x, plane_xdir_y, plane_xdir_z,
         plane_ydir_x, plane_ydir_y, plane_ydir_z,
         start_x, start_y, start_z,
         mid_x, mid_y, mid_z,
         end_x, end_y, end_z]
         """
        units = get_units_from_encoding(coords[2])

        domain = Interval(start=coords[5], end=coords[6])

        # extract plane components
        plane = Plane(
            origin=Point(x=coords[7], y=coords[8], z=coords[9], units=units),
            normal=Vector(x=coords[10], y=coords[11],
                          z=coords[12], units=units),
            xdir=Vector(x=coords[13], y=coords[14], z=coords[15], units=units),
            ydir=Vector(x=coords[16], y=coords[17], z=coords[18], units=units),
            units=units
        )

        # extract points
        start_point = Point(
            x=coords[19], y=coords[20], z=coords[21], units=units)
        mid_point = Point(x=coords[22], y=coords[23],
                          z=coords[24], units=units)
        end_point = Point(x=coords[25], y=coords[26],
                          z=coords[27], units=units)

        return cls(
            plane=plane,
            startPoint=start_point,
            midPoint=mid_point,
            endPoint=end_point,
            domain=domain,
            units=units
        )
