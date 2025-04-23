import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Vector
from specklepy.objects.models.units import Units


def test_vector_creation():
    v = Vector(x=1.0, y=2.0, z=3.0, units=Units.m)
    assert v.x == 1.0
    assert v.y == 2.0
    assert v.z == 3.0
    assert v.units == Units.m.value


def test_vector_length():
    v = Vector(x=3.0, y=4.0, z=0.0, units=Units.m)
    assert v.length == pytest.approx(5.0)  # 3-4-5 triangle


def test_vector_units():
    v = Vector(x=1.0, y=2.0, z=3.0, units=Units.m)
    assert v.units == Units.m.value

    v.units = "mm"
    assert v.units == "mm"


def test_vector_invalid_construction():
    with pytest.raises(TypeError):
        Vector(x=1.0, y=2.0)  # missing z and units


def test_vector_serialization():
    v = Vector(x=1.0, y=2.0, z=3.0, units=Units.m)
    serialized = serialize(v)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Vector)
    assert deserialized.x == v.x
    assert deserialized.y == v.y
    assert deserialized.z == v.z
    assert deserialized.units == v.units
