import pytest
from specklepy.objects.geometry.point import Point
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.core.api.operations import serialize, deserialize


def test_point_creation():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    assert p1.x == 1.0
    assert p1.y == 2.0
    assert p1.z == 3.0
    assert p1.units == Units.m.value


def test_point_distance_calculation():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m)
    p3 = Point(x=1000.0, y=2000.0, z=3000.0, units=Units.mm)

    distance = p1.distance_to(p2)
    expected = ((3.0**2 + 4.0**2 + 5.0**2) ** 0.5)
    assert distance == pytest.approx(expected)

    distance = p1.distance_to(p3)
    assert distance == pytest.approx(0.0)


def test_point_transformation():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = p1.transform_to(transform)
    assert success is True
    assert transformed.x == 3.0
    assert transformed.y == 5.0
    assert transformed.z == 7.0


def test_point_serialization():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    serialized = serialize(p1)
    deserialized = deserialize(serialized)

    assert deserialized.x == p1.x
    assert deserialized.y == p1.y
    assert deserialized.z == p1.z
    assert deserialized.units == p1.units
