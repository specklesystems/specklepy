import pytest
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def sample_vectors():
    return (
        Vector(x=1.0, y=2.0, z=3.0, units=Units.m),
        Vector(x=4.0, y=5.0, z=6.0, units=Units.m)
    )


def test_vector_creation(sample_vectors):
    v1, _ = sample_vectors
    assert v1.x == 1.0
    assert v1.y == 2.0
    assert v1.z == 3.0
    assert v1.units == Units.m.value


def test_vector_length(sample_vectors):
    v1, _ = sample_vectors
    expected = (1.0**2 + 2.0**2 + 3.0**2) ** 0.5
    assert v1.length == pytest.approx(expected)


def test_vector_transformation(sample_vectors):
    v1, _ = sample_vectors
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = v1.transform_to(transform)
    assert success is True
    assert transformed.x == 2.0
    assert transformed.y == 4.0
    assert transformed.z == 6.0
    assert transformed.units == v1.units


def test_vector_serialization(sample_vectors):
    v1, _ = sample_vectors
    serialized = serialize(v1)
    deserialized = deserialize(serialized)

    assert deserialized.x == v1.x
    assert deserialized.y == v1.y
    assert deserialized.z == v1.z
    assert deserialized.units == v1.units


def test_vector_from_list():
    coords = [6, "Objects.Geometry.Vector", 3, 1.0, 2.0, 3.0]
    vector = Vector.from_list(coords, "m")
    assert vector.x == 1.0
    assert vector.y == 2.0
    assert vector.z == 3.0
    assert vector.units == "m"


def test_vector_to_list():
    vector = Vector(x=1.0, y=2.0, z=3.0, units="m")
    coords = vector.to_list()
    assert len(coords) == 6
    assert coords[3:] == [1.0, 2.0, 3.0]
