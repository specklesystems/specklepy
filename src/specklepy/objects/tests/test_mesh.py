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
    faces = [3, 0, 1, 2, 3, 0, 2, 3]  # Two triangles forming a square
    colors = [255, 0, 0, 255] * 4

    return Mesh(
        vertices=vertices,
        faces=faces,
        colors=colors,
        units=Units.m
    )


@pytest.fixture
def cube_mesh():
    vertices = [
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
        1.0, 0.0, 1.0,
        1.0, 1.0, 1.0,
        0.0, 1.0, 1.0
    ]
    faces = [
        3, 0, 1, 2,  # bottom
        3, 0, 2, 3,
        3, 4, 5, 6,  # top
        3, 4, 6, 7,
        3, 0, 1, 5,  # front
        3, 0, 5, 4,
        3, 2, 3, 7,  # back
        3, 2, 7, 6,
        3, 0, 3, 7,  # left
        3, 0, 7, 4,
        3, 1, 2, 6,  # right
        3, 1, 6, 5
    ]
    return Mesh(vertices=vertices, faces=faces, units=Units.m)


def test_mesh_creation(sample_mesh):
    assert sample_mesh.vertices_count == 4
    assert sample_mesh.faces_count == 2
    assert sample_mesh.units == Units.m.value
    assert pytest.approx(sample_mesh.area, 0.001) == 1.0
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
    assert point.x == 1.0  # 0*2 + 1
    assert point.y == 1.0  # 0*2 + 1

    assert pytest.approx(transformed.area, 0.001) == sample_mesh.area * 4
    assert transformed.volume == 0.0


def test_mesh_is_closed(sample_mesh, cube_mesh):
    assert sample_mesh.is_closed() is False
    assert cube_mesh.is_closed() is True


def test_mesh_area_and_volume(sample_mesh, cube_mesh):
    # Test flat square
    assert pytest.approx(sample_mesh.area, 0.001) == 1.0
    assert sample_mesh.volume == 0.0

    # Test cube
    # 1x1x1 cube has 6 faces
    assert pytest.approx(cube_mesh.area, 0.001) == 6.0
    # 1x1x1 cube has volume 1
    assert pytest.approx(cube_mesh.volume, 0.001) == 1.0


def test_mesh_serialization(sample_mesh):
    serialized = serialize(sample_mesh)
    deserialized = deserialize(serialized)

    assert deserialized.vertices == sample_mesh.vertices
    assert deserialized.faces == sample_mesh.faces
    assert deserialized.colors == sample_mesh.colors
    assert deserialized.units == sample_mesh.units
    assert pytest.approx(deserialized.area, 0.001) == sample_mesh.area
    assert pytest.approx(deserialized.volume, 0.001) == sample_mesh.volume


def test_mesh_convert_units(sample_mesh):
    original_area = sample_mesh.area
    sample_mesh.convert_units(Units.mm)
    assert sample_mesh.units == Units.mm.value

    point = sample_mesh.get_point(1)
    assert point.x == 1000.0
    assert point.units == Units.mm.value

    assert pytest.approx(
        sample_mesh.area, 0.001) == original_area * (1000 ** 2)
    assert sample_mesh.volume == 0.0


def test_mesh_to_list():
    mesh = Mesh(
        vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        faces=[3, 0, 1, 2],
        colors=[255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255],
        textureCoordinates=[0.0, 0.0, 1.0, 0.0, 0.0, 1.0],
        units="m"
    )

    coords = mesh.to_list()
    assert len(coords) > 3
    assert coords[0] > 3
    assert coords[1] == "Objects.Geometry.Mesh"

    index = 3
    vertices_count = coords[index]
    assert vertices_count == 9  # 3 vertices * 3 coordinates
    index += 1
    assert coords[index:index + vertices_count] == [0.0,
                                                    0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    index += vertices_count
    faces_count = coords[index]
    assert faces_count == 4  # 1 face with 3 vertices + count
    index += 1
    assert coords[index:index + faces_count] == [3, 0, 1, 2]

    index += faces_count
    colors_count = coords[index]
    assert colors_count == 12  # 3 vertices * 4 rgba values
    index += 1
    assert coords[index:index + colors_count] == [255,
                                                  0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255]

    index += colors_count
    texture_coords_count = coords[index]
    assert texture_coords_count == 6  # 3 vertices * 2 uv coordinates
    index += 1
    assert coords[index:index + texture_coords_count] == [0.0,
                                                          0.0, 1.0, 0.0, 0.0, 1.0]

    index += texture_coords_count
    assert pytest.approx(coords[index], 0.001) == 0.5
    assert coords[index + 1] == 0.0  # volume


def test_mesh_from_list():
    coords = [
        26, "Objects.Geometry.Mesh", 3,  # header
        9,  # vertices count
        0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0,  # vertices
        4,  # faces count
        3, 0, 1, 2,  # faces
        12,  # colors count
        255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255,  # colors
        6,  # texture coordinates count
        0.0, 0.0, 1.0, 0.0, 0.0, 1.0,  # texture coordinates
        0.5, 0.0  # area, volume will be calculated
    ]

    mesh = Mesh.from_list(coords)
    assert mesh.units == "m"
    assert len(mesh.vertices) == 9
    assert mesh.vertices == [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    assert len(mesh.faces) == 4
    assert mesh.faces == [3, 0, 1, 2]
    assert len(mesh.colors) == 12
    assert mesh.colors == [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255]
    assert len(mesh.textureCoordinates) == 6
    assert mesh.textureCoordinates == [0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    assert pytest.approx(mesh.area, 0.001) == 0.5
    assert mesh.volume == 0.0
