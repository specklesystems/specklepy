from dataclasses import dataclass, field
from typing import List, Tuple

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import IHasArea, IHasUnits, IHasVolume


@dataclass(kw_only=True)
class Mesh(
    Base,
    IHasArea,
    IHasVolume,
    IHasUnits,
    speckle_type="Objects.Geometry.Mesh",
    detachable={"vertices", "faces", "colors", "textureCoordinates", "vertexNormals"},
    chunkable={
        "vertices": 31250,
        "faces": 62500,
        "colors": 62500,
        "textureCoordinates": 31250,
        "vertexNormals": 31250,
    },
    serialize_ignore={"vertices_count", "texture_coordinates_count"},
):
    """
    a 3D mesh consisting of vertices and faces
    with optional colors and texture coordinates
    """

    vertices: List[float]
    faces: List[int]
    colors: List[int] = field(default_factory=list)
    textureCoordinates: List[float] = field(default_factory=list)
    vertexNormals: List[float] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"vertices: {self.vertices_count}, "
            f"units: {self.units}, "
            f"has_colors: {len(self.colors) > 0}, "
            f"has_texture_coords: {len(self.textureCoordinates) > 0})"
        )

    @property
    def vertices_count(self) -> int:
        """
        get the number of vertices in the mesh
        """

        if len(self.vertices) % 3 != 0:
            raise ValueError(
                f"Invalid vertices list: length {len(self.vertices)} "
                f"must be a multiple of 3"
            )
        return len(self.vertices) // 3

    @property
    def texture_coordinates_count(self) -> int:
        """
        get the number of texture coordinates in the mesh
        """
        return len(self.textureCoordinates) // 2

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value

    @property
    def volume(self) -> float:
        return self.__dict__.get("_volume", 0.0)

    @volume.setter
    def volume(self, value: float) -> None:
        self.__dict__["_volume"] = value

    def calculate_area(self) -> float:
        """
        calculate total surface area of the mesh
        """
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

        return total_area

    def calculate_volume(self) -> float:
        """
        calculate volume of the mesh if it is closed
        """
        if not self.is_closed():
            return 0.0

        total_volume = 0.0
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

        return abs(total_volume)

    def get_point(self, index: int) -> Point:
        """
        get vertex at index as a Point object
        """
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
                vertices = []
                for j in range(vertex_count):
                    vertex_index = self.faces[i + j + 1]
                    if vertex_index >= self.vertices_count:
                        raise IndexError(f"Vertex index {vertex_index} out of range")
                    vertices.append(self.get_point(vertex_index))
                return vertices

            vertex_count = self.faces[i]
            i += vertex_count + 1
            current_face += 1

        raise IndexError(f"Face index {face_index} out of range")

    def is_closed(self) -> bool:
        """
        check if the mesh is closed (verifying each edge appears twice)
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
