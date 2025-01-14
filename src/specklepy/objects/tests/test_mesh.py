import pytest
from specklepy.objects.geometry.mesh import Mesh
from specklepy.objects.geometry.point import Point
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def sample_mesh():
    vertices = [
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0
    ]
    faces = [3, 0, 1, 2, 3, 0, 2, 3]
    colors = [255, 0, 0, 255] * 4
    area = 1.0
    volume = 0.0

    return Mesh(
        vertices=vertices,
        faces=faces,
        colors=colors,
        units=Units.m,
        area=area,
        volume=volume
    )


def test_mesh_creation(sample_mesh):
    assert sample_mesh.vertices_count == 4
    assert sample_mesh.faces_count == 2
    assert sample_mesh.units == Units.m.value
    assert sample_mesh.area == 1.0
    assert sample_mesh.volume == 0.0


def test_mesh_get_point(sample_mesh):
    point = sample_mesh.get_point(1)
    assert point.x == 1.0
    assert point.y == 0.0
    assert point.z == 0.0
    assert point.units == Units.m.value


def test_mesh_get_points(sample_mesh):
    points = sample_mesh.get_points()
    assert len(points) == 4
    assert all(isinstance(p, Point) for p in points)
    assert points[0].x == 0.0
    assert points[1].x == 1.0


def test_mesh_get_face_vertices(sample_mesh):
    face_vertices = sample_mesh.get_face_vertices(0)
    assert len(face_vertices) == 3
    assert face_vertices[0].x == 0.0
    assert face_vertices[1].x == 1.0
    assert face_vertices[0].units == Units.m.value


def test_mesh_transform(sample_mesh):
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = sample_mesh.transform_to(transform)
    assert success is True

    point = transformed.get_point(0)
    assert point.x == 1.0
    assert point.y == 1.0
    assert transformed.area == sample_mesh.area
    assert transformed.volume == sample_mesh.volume


def test_mesh_is_closed(sample_mesh):
    assert sample_mesh.is_closed() is False

    vertices = [
        0.0, 0.0, 0.0,  # 0
        1.0, 0.0, 0.0,  # 1
        1.0, 1.0, 0.0,  # 2
        0.0, 1.0, 0.0,  # 3
        0.0, 0.0, 1.0,  # 4
        1.0, 0.0, 1.0,  # 5
        1.0, 1.0, 1.0,  # 6
        0.0, 1.0, 1.0   # 7
    ]
    faces = [
        3, 0, 1, 2,  # front
        3, 0, 2, 3,
        3, 4, 5, 6,  # back
        3, 4, 6, 7,
        3, 0, 4, 7,  # left
        3, 0, 7, 3,
        3, 1, 5, 6,  # right
        3, 1, 6, 2,
        3, 3, 2, 6,  # top
        3, 3, 6, 7,
        3, 0, 1, 5,  # bottom
        3, 0, 5, 4
    ]
    closed_mesh = Mesh(vertices=vertices, faces=faces,
                       units=Units.m, area=6.0, volume=1.0)
    assert closed_mesh.is_closed() is True


def test_mesh_serialization(sample_mesh):
    serialized = serialize(sample_mesh)
    deserialized = deserialize(serialized)

    assert deserialized.vertices == sample_mesh.vertices
    assert deserialized.faces == sample_mesh.faces
    assert deserialized.colors == sample_mesh.colors
    assert deserialized.units == sample_mesh.units
    assert deserialized.area == sample_mesh.area
    assert deserialized.volume == sample_mesh.volume


def test_mesh_convert_units(sample_mesh):
    sample_mesh.convert_units(Units.mm)
    assert sample_mesh.units == Units.mm.value

    point = sample_mesh.get_point(1)
    assert point.x == 1000.0
    assert point.units == Units.mm.value

    assert sample_mesh.area == 1.0 * (1000 ** 2)

    assert sample_mesh.volume == 0.0
