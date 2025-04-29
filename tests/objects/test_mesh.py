import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry.mesh import Mesh
from specklepy.objects.geometry.point import Point
from specklepy.objects.models.units import Units


@pytest.fixture
def cube_vertices():
    return [
        -0.5,
        -0.5,
        -0.5,
        0.5,
        -0.5,
        -0.5,
        0.5,
        0.5,
        -0.5,
        -0.5,
        0.5,
        -0.5,
        -0.5,
        -0.5,
        0.5,
        0.5,
        -0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        -0.5,
        0.5,
        0.5,
    ]


@pytest.fixture
def cube_faces():
    return [
        4,
        0,
        3,
        2,
        1,  # bottom (-z)
        4,
        4,
        5,
        6,
        7,  # top (+z)
        4,
        0,
        1,
        5,
        4,  # front (-y)
        4,
        3,
        7,
        6,
        2,  # back (+y)
        4,
        0,
        4,
        7,
        3,  # left (-x)
        4,
        1,
        2,
        6,
        5,  # right (+x)
    ]


@pytest.fixture
def cube_colors():
    return [
        255,
        0,
        0,
        255,  # red
        0,
        255,
        0,
        255,  # green
        0,
        0,
        255,
        255,  # blue
        255,
        255,
        0,
        255,  # yellow
        255,
        0,
        255,
        255,  # magenta
        0,
        255,
        255,
        255,  # cyan
        255,
        255,
        255,
        255,  # white
        0,
        0,
        0,
        255,  # black
    ]


@pytest.fixture
def cube_texture_coords():
    return [
        0.0,
        0.0,
        1.0,
        0.0,
        1.0,
        1.0,
        0.0,
        1.0,
        0.0,
        0.0,
        1.0,
        0.0,
        1.0,
        1.0,
        0.0,
        1.0,
    ]


@pytest.fixture
def sample_mesh(cube_vertices, cube_faces):
    return Mesh(vertices=cube_vertices, faces=cube_faces, units=Units.m)


@pytest.fixture
def full_mesh(cube_vertices, cube_faces, cube_colors, cube_texture_coords):
    return Mesh(
        vertices=cube_vertices,
        faces=cube_faces,
        colors=cube_colors,
        textureCoordinates=cube_texture_coords,
        units=Units.m,
    )


def test_mesh_creation(cube_vertices, cube_faces):
    mesh = Mesh(vertices=cube_vertices, faces=cube_faces, units=Units.m)

    assert mesh.vertices == cube_vertices
    assert mesh.faces == cube_faces
    assert mesh.colors == []
    assert mesh.textureCoordinates == []
    assert mesh.vertexNormals == []
    assert mesh.units == Units.m.value


def test_mesh_vertex_count(sample_mesh):
    assert sample_mesh.vertices_count == 8  # cube has 8 vertices


def test_mesh_texture_coordinates_count(full_mesh):
    assert full_mesh.texture_coordinates_count == 8  # one UV per vertex


def test_mesh_get_point(sample_mesh):
    point = sample_mesh.get_point(0)
    assert isinstance(point, Point)
    assert point.x == -0.5
    assert point.y == -0.5
    assert point.z == -0.5
    assert point.units == sample_mesh.units

    with pytest.raises(IndexError):
        sample_mesh.get_point(8)  # Beyond vertex count


def test_mesh_get_points(sample_mesh):
    points = sample_mesh.get_points()
    assert len(points) == 8
    assert all(isinstance(p, Point) for p in points)
    assert all(p.units == sample_mesh.units for p in points)


def test_mesh_get_texture_coordinate(full_mesh):
    uv = full_mesh.get_texture_coordinate(0)
    assert uv == (0.0, 0.0)

    with pytest.raises(IndexError):
        full_mesh.get_texture_coordinate(8)  # beyond UV count


def test_mesh_get_face_vertices(sample_mesh):
    face_vertices = sample_mesh.get_face_vertices(0)
    assert len(face_vertices) == 4
    assert all(isinstance(v, Point) for v in face_vertices)

    with pytest.raises(IndexError):
        sample_mesh.get_face_vertices(6)  # beyond face count


def test_mesh_is_closed(sample_mesh):
    assert sample_mesh.is_closed()  # cube is a closed mesh


def test_mesh_area(sample_mesh):
    calculated_area = sample_mesh.calculate_area()
    sample_mesh.area = calculated_area
    assert sample_mesh.area == pytest.approx(6.0)


def test_mesh_volume(sample_mesh):
    calculated_volume = sample_mesh.calculate_volume()
    sample_mesh.volume = calculated_volume

    # Verify volume is set correctly
    assert sample_mesh.volume == pytest.approx(1.0)


def test_mesh_invalid_vertices():
    mesh = Mesh(vertices=[0.0, 0.0], faces=[3, 0, 1, 2], units=Units.m)

    with pytest.raises(ValueError):
        _ = mesh.vertices_count


def test_mesh_invalid_faces():
    vertices = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    with pytest.raises(IndexError):
        # Face references vertex index out of range
        mesh = Mesh(vertices=vertices, faces=[3, 0, 1, 5], units=Units.m)
        mesh.get_face_vertices(0)


def test_mesh_serialization(full_mesh):
    serialized = serialize(full_mesh)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Mesh)
    assert deserialized.vertices == full_mesh.vertices
    assert deserialized.faces == full_mesh.faces
    assert deserialized.colors == full_mesh.colors
    assert deserialized.textureCoordinates == full_mesh.textureCoordinates
    assert deserialized.units == full_mesh.units
