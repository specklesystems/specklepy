import math
from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import ICurve, IHasUnits


@dataclass(kw_only=True)
class Arc(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Arc"):
    """
    An arc defined by a plane, start point, mid point and end point.

    This class represents a circular arc in 3D space, defined by three points
    and a plane. The arc is a portion of a circle that lies on the specified plane.

    Attributes:
        plane: The plane on which the arc lies
        startPoint: The starting point of the arc
        midPoint: A point on the arc between the start and end points
        endPoint: The ending point of the arc.


    ```py title="Example"
    from specklepy.objects.geometry.plane import Plane
    from specklepy.objects.geometry.point import Point
    plane = Plane(origin=Point(0, 0, 0), normal=Point(0, 0, 1))
    start = Point(1, 0, 0)
    mid = Point(0.7071, 0.7071, 0)
    end = Point(0, 1, 0)
    arc = Arc(plane=plane, startPoint=start, midPoint=mid, endPoint=end)
    ```
    """

    plane: Plane
    startPoint: Point
    midPoint: Point
    endPoint: Point

    @property
    def radius(self) -> float:
        """Calculates the radius of the arc.

        Returns:
            The radius of the arc, as the distance from the start point to the origin.
        """
        return self.startPoint.distance_to(self.plane.origin)

    @property
    def length(self) -> float:
        """Calculates the length of the arc.

        Returns:
            The length of the arc.
        """
        start_to_mid = self.startPoint.distance_to(self.midPoint)
        mid_to_end = self.midPoint.distance_to(self.endPoint)
        r = self.radius
        angle = (2 * math.asin(start_to_mid / (2 * r))) + (
            2 * math.asin(mid_to_end / (2 * r))
        )
        return r * angle

    @property
    def measure(self) -> float:
        """Calculates the angular measure of the arc in radians.

        Returns:
            The angular measure of the arc in radians.
        """
        start_to_mid = self.startPoint.distance_to(self.midPoint)
        mid_to_end = self.midPoint.distance_to(self.endPoint)
        r = self.radius
        return (2 * math.asin(start_to_mid / (2 * r))) + (
            2 * math.asin(mid_to_end / (2 * r))
        )
