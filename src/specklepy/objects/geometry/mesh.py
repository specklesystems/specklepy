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
    area: float = field(init=False)
    volume: float = field(init=False)
    _vertices_count: int = field(init=False, repr=False)

    def __post_init__(self):
        """
        calculate initial values and validate vertices
        """
        if not self.vertices:
            self._vertices_count = 0
        else:
            if len(self.vertices) % 3 != 0:
                raise ValueError(
                    f"Invalid vertices list: length ({len(
                        self.vertices)}) must be a multiple of 3"
                )
            self._vertices_count = len(self.vertices) // 3

        self._calculate_area_and_volume()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"vertices: {self._vertices_count}, "
            f"faces: {self.faces_count}, "
            f"units: {self.units}, "
            f"has_colors: {len(self.colors) > 0}, "
            f"has_texture_coords: {len(self.textureCoordinates) > 0})"
        )

    def _calculate_area_and_volume(self):
        """
        internal method to update area and volume calculations
        """
        # Calculate area
        total_area = 0.0
        face_index = 0
        i = 0

        while i < len(self.faces):
            vertex_count = self.faces[i]
            if vertex_count >= 3:
                face_vertices = self.get_face_vertices(face_index)
                for j in range(1, vertex_count - 1):
                    v0 = face_vertices[0]
                    v1 = face_vertices[j]
                    v2 = face_vertices[j + 1]
                    a = [v1.x - v0.x, v1.y - v0.y, v1.z - v0.z]
                    b = [v2.x - v0.x, v2.y - v0.y, v2.z - v0.z]
                    cx = a[1] * b[2] - a[2] * b[1]
                    cy = a[2] * b[0] - a[0] * b[2]
                    cz = a[0] * b[1] - a[1] * b[0]
                    area = 0.5 * (cx * cx + cy * cy + cz * cz) ** 0.5
                    total_area += area
            i += vertex_count + 1
            face_index += 1

        self.area = total_area

        # Calculate volume
        total_volume = 0.0
        if self.is_closed():
            face_index = 0
            i = 0
            while i < len(self.faces):
                vertex_count = self.faces[i]
                if vertex_count >= 3:
                    face_vertices = self.get_face_vertices(face_index)
                    v0 = face_vertices[0]
                    for j in range(1, vertex_count - 1):
                        v1 = face_vertices[j]
                        v2 = face_vertices[j + 1]
                        a = [v0.x, v0.y, v0.z]
                        b = [v1.x - v0.x, v1.y - v0.y, v1.z - v0.z]
                        c = [v2.x - v0.x, v2.y - v0.y, v2.z - v0.z]
                        cx = b[1] * c[2] - b[2] * c[1]
                        cy = b[2] * c[0] - b[0] * c[2]
                        cz = b[0] * c[1] - b[1] * c[0]
                        v = (a[0] * cx + a[1] * cy + a[2] * cz) / 6.0
                        total_volume += v
                i += vertex_count + 1
                face_index += 1

        self.volume = abs(total_volume)

    @property
    def vertices_count(self) -> int:
        """
        get the number of vertices in the mesh.
        """
        return self._vertices_count

    @property
    def faces_count(self) -> int:
        """
        get the number of faces in the mesh.
        """
        count = 0
        i = 0
        while i < len(self.faces):
            n = self.faces[i]
            count += 1
            i += n + 1
        return count

    @property
    def texture_coordinates_count(self) -> int:
        """
        get the number of texture coordinates in the mesh.
        """
        return len(self.textureCoordinates) // 2

    def get_point(self, index: int) -> Point:
        """
        get vertex at index as a Point object.
        """
        if index < 0 or index >= self._vertices_count:  # use cached count
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
        get all vertices as Point objects.
        """
        return [self.get_point(i) for i in range(self._vertices_count)]  # use cached count

    def get_texture_coordinate(self, index: int) -> Tuple[float, float]:
        """
        get texture coordinate at index.
        """
        if index < 0 or index >= self.texture_coordinates_count:
            raise IndexError(f"Texture coordinate index {index} out of range")

        index *= 2
        return (self.textureCoordinates[index], self.textureCoordinates[index + 1])

    def get_face_vertices(self, face_index: int) -> List[Point]:
        """
        get the vertices of a specific face.
        """
        i = 0
        current_face = 0

        while i < len(self.faces):
            if current_face == face_index:
                vertex_count = self.faces[i]
                vertices = []
                for j in range(vertex_count):
                    vertex_index = self.faces[i + j + 1]
                    if vertex_index >= self._vertices_count:  # use cached count
                        raise IndexError(
                            f"Vertex index {vertex_index} out of range")
                    vertices.append(self.get_point(vertex_index))
                return vertices

            # skip this face and move to next
            vertex_count = self.faces[i]
            i += vertex_count + 1
            current_face += 1

        raise IndexError(f"Face index {face_index} out of range")

    def transform_to(self, transform) -> Tuple[bool, "Mesh"]:
        """
        transform this mesh using the given transform.
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

        transformed = Mesh(
            vertices=transformed_vertices,
            faces=self.faces.copy(),
            colors=self.colors.copy(),
            textureCoordinates=self.textureCoordinates.copy(),
            units=self.units,
            applicationId=self.applicationId
        )

        return True, transformed

    def convert_units(self, to_units: str | Units) -> None:
        """
        convert the mesh vertices to different units.
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
        self._calculate_area_and_volume()

    def is_closed(self) -> bool:
        """
        check if the mesh is closed by verifying each edge appears exactly twice.
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
        """
        Returns a serializable list of format:
        [total_length, speckle_type, units_encoding,
         vertices_count, v1x, v1y, v1z, v2x, v2y, v2z, ...,
         faces_count, f1, f2, f3, ...,
         colors_count, c1, c2, c3, ...,
         texture_coords_count, t1u, t1v, t2u, t2v, ...,
         area, volume]
        """
        self._calculate_area_and_volume()

        result = []

        # add vertices
        result.append(len(self.vertices))
        result.extend(self.vertices)

        # add faces
        result.append(len(self.faces))
        result.extend(self.faces)

        # add colors (if any)
        result.append(len(self.colors))
        if self.colors:
            result.extend(self.colors)

        # add texture coordinates (if any)
        result.append(len(self.textureCoordinates))
        if self.textureCoordinates:
            result.extend(self.textureCoordinates)

        # add area and volume (calculated properties)
        result.extend([self.area, self.volume])

        # add header information
        result.insert(0, get_encoding_from_units(self.units))
        result.insert(0, self.speckle_type)
        result.insert(0, len(result) + 1)
        return result

    @classmethod
    def from_list(cls, coords: List[Any]) -> "Mesh":
        """
        Creates a Mesh from a list of format:
        [total_length, speckle_type, units_encoding,
         vertices_count, v1x, v1y, v1z, v2x, v2y, v2z, ...,
         faces_count, f1, f2, f3, ...,
         colors_count, c1, c2, c3, ...,
         texture_coords_count, t1u, t1v, t2u, t2v, ...,
         area, volume]
        """
        units = get_units_from_encoding(coords[2])

        index = 3

        vertices_count = int(coords[index])
        index += 1
        vertices = coords[index:index + vertices_count]
        index += vertices_count

        faces_count = int(coords[index])
        index += 1
        faces = [int(f) for f in coords[index:index + faces_count]]
        index += faces_count

        colors_count = int(coords[index])
        index += 1
        colors = []
        if colors_count > 0:
            colors = [int(c) for c in coords[index:index + colors_count]]
            index += colors_count

        texture_coords_count = int(coords[index])
        index += 1
        texture_coords = []
        if texture_coords_count > 0:
            texture_coords = coords[index:index + texture_coords_count]
            index += texture_coords_count

        return cls(
            vertices=vertices,
            faces=faces,
            colors=colors,
            textureCoordinates=texture_coords,
            units=units
        )
