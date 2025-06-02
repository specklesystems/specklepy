import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Point
from specklepy.objects.models.units import Units


def test_point_creation():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    assert p1.x == 1.0
    assert p1.y == 2.0
    assert p1.z == 3.0
    assert p1.units == Units.m.value


def test_point_distance_calculation():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m)

    distance = p1.distance_to(p2)
    expected = (3.0**2 + 4.0**2 + 5.0**2) ** 0.5
    assert distance == pytest.approx(expected)

    with pytest.raises(TypeError):
        p1.distance_to("not a point")


def test_point_serialization():
    p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.mm)
    serialized = serialize(p1)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Point)
    assert deserialized.x == p1.x
    assert deserialized.y == p1.y
    assert deserialized.z == p1.z
    assert deserialized.units == p1.units
