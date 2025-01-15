from dataclasses import dataclass, field
from typing import List, Tuple, Any

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import IHasArea, IHasVolume, IHasUnits, ITransformable
from specklepy.objects.models.units import (
    Units,
    get_scale_factor,
    get_units_from_string,
    get_units_from_encoding,
    get_encoding_from_units
)


@dataclass(kw_only=True)
class Mesh(
    Base,
    IHasArea,
    IHasVolume,
    IHasUnits,
    ITransformable,
    speckle_type="Objects.Geometry.Mesh",
    detachable={"vertices", "faces", "colors", "textureCoordinates"},
    chunkable={
        "vertices": 31250,
        "faces": 62500,
        "colors": 62500,
        "textureCoordinates": 31250,
    },
):
    """
    a 3D mesh consisting of vertices and faces with optional colors and texture coordinates.
    """

    vertices: List[float]
    faces: List[int]
    colors: List[int] = field(default_factory=list)
    textureCoordinates: List[float] = field(default_factory=list)
    _area: float = field(default=0.0, init=False, repr=False)
    _volume: float = field(default=0.0, init=False, repr=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"vertices: {self.vertices_count}, "
            f"faces: {self.faces_count}, "
            f"units: {self.units}, "
            f"has_colors: {len(self.colors) > 0}, "
            f"has_texture_coords: {len(self.textureCoordinates) > 0})"
        )

    @property
    def vertices_count(self) -> int:
        return len(self.vertices) // 3

    @property
    def faces_count(self) -> int:
        count = 0
        i = 0
        while i < len(self.faces):
            n = self.faces[i]
            count += 1
            i += n + 1
        return count

    @property
    def texture_coordinates_count(self) -> int:
        return len(self.textureCoordinates) // 2

    def get_point(self, index: int) -> Point:
        if index < 0 or index >= self.vertices_count:
            raise IndexError(f"Vertex index {index} out of range")

        index *= 3
        return Point(
            x=self.vertices[index],
            y=self.vertices[index + 1],
            z=self.vertices[index + 2],
            units=self.units,
        )

    def get_points(self) -> List[Point]:
        """
        get all vertices as Point objects
        """
        return [self.get_point(i) for i in range(self.vertices_count)]

    def get_texture_coordinate(self, index: int) -> Tuple[float, float]:
        """
        get texture coordinate at index
        """
        if index < 0 or index >= self.texture_coordinates_count:
            raise IndexError(f"Texture coordinate index {index} out of range")

        index *= 2
        return (self.textureCoordinates[index], self.textureCoordinates[index + 1])

    def get_face_vertices(self, face_index: int) -> List[Point]:
        """
        get the vertices of a specific face
        """
        i = 0
        current_face = 0

        while i < len(self.faces):
            if current_face == face_index:
                vertex_count = self.faces[i]
                return [self.get_point(self.faces[i + j]) for j in range(1, vertex_count + 1)]

            vertex_count = self.faces[i]
            i += vertex_count + 1
            current_face += 1

        raise IndexError(f"Face index {face_index} out of range")

    def transform_to(self, transform) -> Tuple[bool, "Mesh"]:
        """
        transform this mesh using the given transform
        """
        transformed_vertices = []

        for i in range(0, len(self.vertices), 3):
            point = Point(
                x=self.vertices[i],
                y=self.vertices[i + 1],
                z=self.vertices[i + 2],
                units=self.units
            )
            success, transformed_point = point.transform_to(transform)
            if not success:
                return False, self

            transformed_vertices.extend([
                transformed_point.x,
                transformed_point.y,
                transformed_point.z
            ])

        current_area = self._area
        current_volume = self._volume

        transformed = Mesh(
            vertices=transformed_vertices,
            faces=self.faces.copy(),
            colors=self.colors.copy(),
            textureCoordinates=self.textureCoordinates.copy(),
            units=self.units,
            applicationId=self.applicationId,
            area=current_area,
            volume=current_volume
        )

        return True, transformed

    def convert_units(self, to_units: str | Units) -> None:
        """
        convert the mesh vertices to different units
        """
        if isinstance(to_units, Units):
            to_units = to_units.value

        scale_factor = get_scale_factor(
            get_units_from_string(self.units),
            get_units_from_string(to_units)
        )

        for i in range(len(self.vertices)):
            self.vertices[i] *= scale_factor

        self.units = to_units

        self._area *= scale_factor * scale_factor
        self._volume *= scale_factor * scale_factor * scale_factor

    def is_closed(self) -> bool:
        """
        check if the mesh is closed
        """
        edge_counts = {}

        i = 0
        while i < len(self.faces):
            vertex_count = self.faces[i]
            for j in range(vertex_count):
                v1 = self.faces[i + 1 + j]
                v2 = self.faces[i + 1 + ((j + 1) % vertex_count)]
                edge = tuple(sorted([v1, v2]))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1

            i += vertex_count + 1

        return all(count == 2 for count in edge_counts.values())

    def to_list(self) -> List[Any]:
        """Returns a serializable list of format:
        [total_length, speckle_type, units_encoding,
         vertices_count, v1x, v1y, v1z, v2x, v2y, v2z, ...,
         faces_count, f1, f2, f3, ...,
         colors_count, c1, c2, c3, ...,
         texture_coords_count, t1u, t1v, t2u, t2v, ...,
         area, volume]"""
        result = []

        # Add vertices
        result.append(len(self.vertices))
        result.extend(self.vertices)

        # Add faces
        result.append(len(self.faces))
        result.extend(self.faces)

        # Add colors (if any)
        result.append(len(self.colors))
        if self.colors:
            result.extend(self.colors)

        # Add texture coordinates (if any)
        result.append(len(self.textureCoordinates))
        if self.textureCoordinates:
            result.extend(self.textureCoordinates)

        # Add area and volume
        result.extend([self.area, self.volume])

        # Add header information
        result.insert(0, get_encoding_from_units(self.units))
        result.insert(0, self.speckle_type)
        result.insert(0, len(result) + 1)
        return result

    @classmethod
    def from_list(cls, coords: List[Any]) -> "Mesh":
        """Creates a Mesh from a list of format:
        [total_length, speckle_type, units_encoding,
         vertices_count, v1x, v1y, v1z, v2x, v2y, v2z, ...,
         faces_count, f1, f2, f3, ...,
         colors_count, c1, c2, c3, ...,
         texture_coords_count, t1u, t1v, t2u, t2v, ...,
         area, volume]"""
        units = get_units_from_encoding(coords[2])

        index = 3

        # Extract vertices
        vertices_count = int(coords[index])
        index += 1
        vertices = coords[index:index + vertices_count]
        index += vertices_count

        # Extract faces
        faces_count = int(coords[index])
        index += 1
        faces = [int(f) for f in coords[index:index + faces_count]]
        index += faces_count

        # Extract colors
        colors_count = int(coords[index])
        index += 1
        colors = []
        if colors_count > 0:
            colors = [int(c) for c in coords[index:index + colors_count]]
            index += colors_count

        # Extract texture coordinates
        texture_coords_count = int(coords[index])
        index += 1
        texture_coords = []
        if texture_coords_count > 0:
            texture_coords = coords[index:index + texture_coords_count]
            index += texture_coords_count

        # Extract area and volume
        area = coords[index]
        volume = coords[index + 1]

        return cls(
            vertices=vertices,
            faces=faces,
            colors=colors,
            textureCoordinates=texture_coords,
            area=area,
            volume=volume,
            units=units
        )
