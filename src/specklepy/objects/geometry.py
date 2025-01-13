from dataclasses import dataclass, field
from typing import List, Tuple
import math

from specklepy.objects.base import Base
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits, IHasVolume, ITransformable
from specklepy.objects.models.units import (
    Units,
    get_encoding_from_units,
    get_scale_factor,
    get_units_from_string,
    get_units_from_encoding
)
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Point(Base, IHasUnits, ITransformable, speckle_type="Objects.Geometry.Point"):
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
    def from_list(cls, coords: List[float], units: str | Units) -> "Point":
        return cls(x=coords[0], y=coords[1], z=coords[2], units=units)

    @classmethod
    def from_coords(cls, x: float, y: float, z: float, units: str | Units) -> "Point":
        return cls(x=x, y=y, z=z, units=units)

    def transform_to(self, transform) -> Tuple[bool, "Point"]:
        """
        transform this point using the given transform
        """
        m = transform.matrix
        tx = self.x * m[0] + self.y * m[1] + self.z * m[2] + m[3]
        ty = self.x * m[4] + self.y * m[5] + self.z * m[6] + m[7]
        tz = self.x * m[8] + self.y * m[9] + self.z * m[10] + m[11]

        transformed = Point(
            x=tx,
            y=ty,
            z=tz,
            units=self.units,
            applicationId=self.applicationId
        )
        return True, transformed

    def distance_to(self, other: "Point") -> float:
        """
        calculates the distance between this point and another given point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"Expected Point object, got {type(other)}")

        # if units are the same perform direct calculation
        if self.units == other.units:
            dx = other.x - self.x
            dy = other.y - self.y
            dz = other.z - self.z
            return (dx * dx + dy * dy + dz * dz) ** 0.5

        # convert other point's coordinates to this point's units
        scale_factor = get_scale_factor(
            get_units_from_string(
                other.units), get_units_from_string(self.units)
        )

        dx = (other.x * scale_factor) - self.x
        dy = (other.y * scale_factor) - self.y
        dz = (other.z * scale_factor) - self.z

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
    def from_list(cls, coords: List[float], units: str | Units) -> "Line":
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
        units: str,
    ) -> "Line":
        start = Point(x=start_x, y=start_y, z=start_z, units=units)
        end = Point(x=end_x, y=end_y, z=end_z, units=units)
        return cls(start=start, end=end, units=units)


@dataclass(kw_only=True)
class Polyline(Base, IHasUnits, ICurve, speckle_type="Objects.Geometry.Polyline"):
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


@dataclass(kw_only=True)
class Mesh(
    Base,
    IHasArea,
    IHasVolume,
    IHasUnits,
    speckle_type="Objects.Geometry.Mesh",
    detachable={"vertices", "faces", "colors", "textureCoordinates"},
    chunkable={
        "vertices": 31250,
        "faces": 62500,
        "colors": 62500,
        "textureCoordinates": 31250,
    },
):

    vertices: List[float]
    faces: List[int]
    colors: List[int] = field(default_factory=list)
    textureCoordinates: List[float] = field(default_factory=list)

    @property
    def vertices_count(self) -> int:
        return len(self.vertices) // 3

    @property
    def texture_coordinates_count(self) -> int:
        return len(self.textureCoordinates) // 2

    def get_point(self, index: int) -> Point:

        index *= 3
        return Point(
            x=self.vertices[index],
            y=self.vertices[index + 1],
            z=self.vertices[index + 2],
            units=self.units,
        )

    def get_points(self) -> List[Point]:

        if len(self.vertices) % 3 != 0:
            raise ValueError(
                "Mesh vertices list is malformed: expected length to be multiple of 3"
            )

        points = []
        for i in range(0, len(self.vertices), 3):
            points.append(
                Point(
                    x=self.vertices[i],
                    y=self.vertices[i + 1],
                    z=self.vertices[i + 2],
                    units=self.units,
                )
            )
        return points

    def get_texture_coordinate(self, index: int) -> Tuple[float, float]:

        index *= 2
        return (self.textureCoordinates[index], self.textureCoordinates[index + 1])

    def align_vertices_with_texcoords_by_index(self) -> None:

        if not self.textureCoordinates:
            return

        if self.texture_coordinates_count == self.vertices_count:
            return

        faces_unique = []
        vertices_unique = []
        has_colors = len(self.colors) > 0
        colors_unique = [] if has_colors else None

        n_index = 0
        while n_index < len(self.faces):
            n = self.faces[n_index]
            if n < 3:
                n += 3

            if n_index + n >= len(self.faces):
                break

            faces_unique.append(n)
            for i in range(1, n + 1):
                vert_index = self.faces[n_index + i]
                new_vert_index = len(vertices_unique) // 3

                point = self.get_point(vert_index)
                vertices_unique.extend([point.x, point.y, point.z])

                if colors_unique is not None:
                    colors_unique.append(self.colors[vert_index])
                faces_unique.append(new_vert_index)

            n_index += n + 1

        self.vertices = vertices_unique
        self.colors = colors_unique if colors_unique is not None else self.colors
        self.faces = faces_unique


@dataclass(kw_only=True)
class Vector(Base, IHasUnits, ITransformable, speckle_type="Objects.Geometry.Vector"):
    """
    a 3-dimensional vector
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, units: {self.units})"

    @property
    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_list(cls, coords: List[float], units: str | Units) -> "Vector":
        return cls(x=coords[0], y=coords[1], z=coords[2], units=units)

    def transform_to(self, transform):
        m = transform.matrix
        tx = self.x * m[0] + self.y * m[1] + self.z * m[2]
        ty = self.x * m[4] + self.y * m[5] + self.z * m[6]
        tz = self.x * m[8] + self.y * m[9] + self.z * m[10]
        transformed = Vector(x=tx, y=ty, z=tz, units=self.units,
                             applicationId=self.applicationId)
        return True, transformed


@dataclass(kw_only=True)
class Plane(Base, ITransformable, IHasUnits, speckle_type="Objects.Geometry.Plane"):
    """
    A 3-dimensional Plane consisting of an origin Point, and 3 Vectors as its X, Y and Z axis.
    """

    origin: Point
    normal: Vector
    xdir: Vector
    ydir: Vector

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"origin: {self.origin}, "
            f"normal: {self.normal}, "
            f"xdir: {self.xdir}, "
            f"ydir: {self.ydir}, "
            f"units: {self.units})"
        )

    def to_list(self) -> List[float]:
        """
        Returns the values of this Plane as a list of numbers
        """
        result = []
        result.extend(self.origin.to_list())
        result.extend(self.normal.to_list())
        result.extend(self.xdir.to_list())
        result.extend(self.ydir.to_list())
        result.append(get_encoding_from_units(self.units))
        return result

    @classmethod
    def from_list(cls, coords: List[float]) -> "Plane":
        """
        Creates a new Plane based on a list of values and the unit they're drawn in.

        Args:
            coords: The list of values representing this plane

        Returns:
            A new Plane with the provided values
        """
        units = get_units_from_encoding(int(coords[-1]))

        plane = cls(
            origin=Point(x=coords[0], y=coords[1], z=coords[2], units=units),
            normal=Vector(x=coords[3], y=coords[4], z=coords[5], units=units),
            xdir=Vector(x=coords[6], y=coords[7], z=coords[8], units=units),
            ydir=Vector(x=coords[9], y=coords[10], z=coords[11], units=units),
            units=units,
        )

        return plane

    def transform_to(self, transform) -> Tuple[bool, Base]:
        """
        Transform this plane using the given transform

        Args:
            transform: The transform to apply

        Returns:
            Tuple of (success, transformed plane)
        """
        _, transformed_origin = self.origin.transform_to(transform)
        _, transformed_normal = self.normal.transform_to(transform)
        _, transformed_xdir = self.xdir.transform_to(transform)
        _, transformed_ydir = self.ydir.transform_to(transform)

        transformed = Plane(
            origin=transformed_origin,
            normal=transformed_normal,
            xdir=transformed_xdir,
            ydir=transformed_ydir,
            applicationId=self.applicationId,
            units=self.units,
        )

        return True, transformed


@dataclass(kw_only=True)
class Arc(Base, ICurve, IHasUnits, ITransformable, speckle_type="Objects.Geometry.Arc"):
    """
    Represents a sub-curve of a three-dimensional circle.

    The plane's origin is the Arc center. The plane normal indicates the handedness 
    of the Arc such that direction from startPoint to endPoint is counterclockwise.
    """

    plane: Plane
    startPoint: Point
    midPoint: Point
    endPoint: Point
    domain: Interval = field(default_factory=Interval.unit_interval)

    @property
    def radius(self) -> float:
        """The radius of the Arc"""
        return self.startPoint.distance_to(self.plane.origin)

    @property
    def measure(self) -> float:
        """
        The measure of the Arc in radians.
        Calculated using the arc addition postulate using the midPoint.
        """
        start_to_mid = self.startPoint.distance_to(self.midPoint)
        mid_to_end = self.midPoint.distance_to(self.endPoint)
        r = self.radius
        return (2 * math.asin(start_to_mid / (2 * r))) + (2 * math.asin(mid_to_end / (2 * r)))

    @property
    def length(self) -> float:
        """The length of the Arc"""
        return self.radius * self.measure

    @property
    def _domain(self) -> Interval:
        """Internal domain property for ICurve interface"""
        return self.domain

    def transform_to(self, transform) -> Tuple[bool, "Arc"]:
        """
        Transform this arc using the given transform

        Args:
            transform: The transform to apply

        Returns:
            Tuple of (success, transformed arc)
        """
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
        """
        Returns the values of this Arc as a list of numbers.
        This is only used for serialization purposes.
        """
        from specklepy.objects.models.units import get_encoding_from_units

        result = []
        result.append(self.radius)
        result.append(0)  # Backwards compatibility: start angle
        result.append(0)  # Backwards compatibility: end angle
        result.append(self.measure)
        result.append(self.domain.start)
        result.append(self.domain.end)
        result.extend(self.plane.to_list())
        result.extend(self.startPoint.to_list())
        result.extend(self.midPoint.to_list())
        result.extend(self.endPoint.to_list())
        result.append(get_encoding_from_units(self.units))

        # Add type encoding and total length at start
        result.insert(0, 1)  # CurveTypeEncoding.Arc = 1
        result.insert(0, len(result))
        return result

    @classmethod
    def from_list(cls, coords: List[float]) -> "Arc":
        """
        Creates a new Arc based on a list of values.
        This is only used for deserialization purposes.

        Args:
            coords: The list of values representing this arc

        Returns:
            A new Arc with the values assigned from the list
        """
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
