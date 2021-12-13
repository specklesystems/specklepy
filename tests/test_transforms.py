from typing import List
import pytest
from specklepy.api import operations
from specklepy.objects.geometry import Mesh, Point, Vector
from specklepy.objects.other import (
    Transform,
    BlockInstance,
    BlockDefinition,
    IDENTITY_TRANSFORM,
)


@pytest.fixture()
def point():
    return Point(x=1, y=10, z=2)


@pytest.fixture()
def points():
    return [Point(x=1 + i, y=10 + i, z=2 + i) for i in range(5)]


@pytest.fixture()
def point_value():
    return [1, 10, 2]


@pytest.fixture()
def points_values():
    coords = []
    for i in range(5):
        coords.extend([1 + i, 10 + i, 2 + 1])
    return coords


@pytest.fixture()
def vector():
    return Vector(x=1, y=10, z=2)


@pytest.fixture()
def vector_value():
    return [1, 1, 2]


@pytest.fixture()
def mesh():
    return Mesh(
        vertices=[-7, 5, 1, -8, 4, 0, -7, 3, 0, -6, 4, 0],
        faces=[1, 1, 2, 3, 0],
        units="feet",
    )


@pytest.fixture()
def transform():
    """Translates to [1, 2, 0] and scales z by 0.5"""
    return Transform.from_list(
        [
            1.0,
            0.0,
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            2.0,
            0.0,
            0.0,
            0.5,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
    )


def test_point_transform(point: Point, transform: Transform):
    new_point = transform.apply_to_point(point)

    assert new_point.x == point.x + 1
    assert new_point.y == point.y + 2
    assert new_point.z == point.z * 0.5


def test_points_transform(points: List[Point], transform: Transform):
    new_points = transform.apply_to_points(points)

    for (i, new_point) in enumerate(new_points):
        assert new_point.x == points[i].x + 1
        assert new_point.y == points[i].y + 2
        assert new_point.z == points[i].z * 0.5


def test_point_value_transform(point_value: List[float], transform: Transform):
    new_coords = transform.apply_to_point_value(point_value)

    assert new_coords[0] == point_value[0] + 1
    assert new_coords[1] == point_value[1] + 2
    assert new_coords[2] == point_value[2] * 0.5


def test_points_values_transform(points_values: List[float], transform: Transform):
    new_coords = transform.apply_to_points_values(points_values)

    for i in range(0, len(points_values), 3):
        assert new_coords[i] == points_values[i] + 1
        assert new_coords[i + 1] == points_values[i + 1] + 2
        assert new_coords[i + 2] == points_values[i + 2] * 0.5


def test_vector_transform(vector: Vector, transform: Transform):
    new_vector = transform.apply_to_vector(vector)

    assert new_vector.x == vector.x
    assert new_vector.y == vector.y
    assert new_vector.z == vector.z * 0.5


def test_vector_value_transform(vector_value: List[float], transform: Transform):
    new_coords = transform.apply_to_vector_value(vector_value)

    assert new_coords[0] == vector_value[0]
    assert new_coords[1] == vector_value[1]
    assert new_coords[2] == vector_value[2] * 0.5


def test_transform_fails_with_malformed_value():
    with pytest.raises(ValueError):
        Transform.from_list("asdf")
    with pytest.raises(ValueError):
        Transform.from_list([7, 8, 9])


def test_transform_serialisation(transform: Transform):
    serialized = operations.serialize(transform)
    deserialized = operations.deserialize(serialized)

    assert transform.get_id() == deserialized.get_id()


def test_mesh_transform(mesh: Mesh, transform: Transform):
    new_mesh = mesh.transform_to(transform)

    assert mesh.vertices != new_mesh.vertices

    new_mesh.vertices = mesh.vertices

    assert mesh.get_id() == new_mesh.get_id()