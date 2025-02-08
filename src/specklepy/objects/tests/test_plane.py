import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Plane, Point, Vector
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_point():
    point = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    return point


@pytest.fixture
def sample_vectors():
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

    return normal, xdir, ydir


@pytest.fixture
def sample_plane(sample_point, sample_vectors):
    normal, xdir, ydir = sample_vectors
    plane = Plane(
        origin=sample_point, normal=normal, xdir=xdir, ydir=ydir, units=Units.m
    )
    return plane


def test_plane_creation(sample_point, sample_vectors):
    normal, xdir, ydir = sample_vectors
    plane = Plane(
        origin=sample_point, normal=normal, xdir=xdir, ydir=ydir, units=Units.m
    )

    assert plane.origin == sample_point
    assert plane.normal == normal
    assert plane.xdir == xdir
    assert plane.ydir == ydir
    assert plane.units == Units.m.value


def test_plane_units(sample_point, sample_vectors):
    normal, xdir, ydir = sample_vectors
    plane = Plane(
        origin=sample_point, normal=normal, xdir=xdir, ydir=ydir, units=Units.m
    )

    assert plane.units == Units.m.value

    plane.units = "mm"
    assert plane.units == "mm"


def test_plane_invalid_construction():
    point = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

    with pytest.raises(Exception):
        Plane(origin="not a point", normal=normal, xdir=xdir, ydir=ydir)

    with pytest.raises(Exception):
        Plane(origin=point, normal="not a vector", xdir=xdir, ydir=ydir)

    with pytest.raises(Exception):
        Plane(origin=point, normal=normal, xdir="not a vector", ydir=ydir)

    # Test with invalid ydir vector
    with pytest.raises(Exception):
        Plane(origin=point, normal=normal, xdir=xdir, ydir="not a vector")


def test_plane_serialization(sample_plane):
    serialized = serialize(sample_plane)
    deserialized = deserialize(serialized)

    # Check all properties are preserved
    assert deserialized.origin.x == sample_plane.origin.x
    assert deserialized.origin.y == sample_plane.origin.y
    assert deserialized.origin.z == sample_plane.origin.z

    assert deserialized.normal.x == sample_plane.normal.x
    assert deserialized.normal.y == sample_plane.normal.y
    assert deserialized.normal.z == sample_plane.normal.z

    assert deserialized.xdir.x == sample_plane.xdir.x
    assert deserialized.xdir.y == sample_plane.xdir.y
    assert deserialized.xdir.z == sample_plane.xdir.z

    assert deserialized.ydir.x == sample_plane.ydir.x
    assert deserialized.ydir.y == sample_plane.ydir.y
    assert deserialized.ydir.z == sample_plane.ydir.z

    assert deserialized.units == sample_plane.units
