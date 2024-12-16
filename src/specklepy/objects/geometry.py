from dataclasses import dataclass, field
from typing import List, Tuple
from specklepy.objects.base import Base
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits, IHasVolume
from specklepy.objects.models.units import Units, get_encoding_from_units
from specklepy.objects.primitive import Interval


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
    def from_list(cls, coords: List[float], units: str | Units) -> "Point":
        return cls(x=coords[0], y=coords[1], z=coords[2], units=units)

    @classmethod
    def from_coords(cls, x: float, y: float, z: float, units: str | Units) -> "Point":
        return cls(x=x, y=y, z=z, units=units)

    def distance_to(self, other: "Point") -> float:
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
    def from_list(cls, coords: List[float], units: str) -> "Line":
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
                "Polyline value list is malformed: expected length to be multiple of 3")

        points = []
        for i in range(0, len(self.value), 3):
            points.append(
                Point(
                    x=self.value[i],
                    y=self.value[i + 1],
                    z=self.value[i + 2],
                    units=self.units
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
            value=coords[6:6 + point_count],
            units=units
        )


@dataclass(kw_only=True)
class Mesh(Base, IHasArea, IHasVolume, IHasUnits,
           speckle_type="Objects.Geometry.Mesh",
           detachable={"vertices", "faces", "colors", "textureCoordinates"},
           chunkable={"vertices": 31250, "faces": 62500, "colors": 62500, "textureCoordinates": 31250}):

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
            units=self.units
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
                    units=self.units
                )
            )
        return points

    def get_texture_coordinate(self, index: int) -> Tuple[float, float]:

        index *= 2
        return (
            self.textureCoordinates[index],
            self.textureCoordinates[index + 1]
        )

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
