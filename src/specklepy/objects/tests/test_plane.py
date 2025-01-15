import pytest
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def sample_plane():
    return Plane(
        origin=Point(x=0.0, y=0.0, z=0.0, units=Units.m),
        normal=Vector(x=0.0, y=0.0, z=1.0, units=Units.m),
        xdir=Vector(x=1.0, y=0.0, z=0.0, units=Units.m),
        ydir=Vector(x=0.0, y=1.0, z=0.0, units=Units.m),
        units=Units.m
    )


def test_plane_creation(sample_plane):
    assert sample_plane.origin.x == 0.0
    assert sample_plane.normal.z == 1.0
    assert sample_plane.xdir.x == 1.0
    assert sample_plane.ydir.y == 1.0
    assert sample_plane.units == Units.m.value


def test_plane_transformation(sample_plane):
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = sample_plane.transform_to(transform)
    assert success is True
    assert transformed.origin.x == 1.0
    assert transformed.xdir.x == 2.0
    assert transformed.units == sample_plane.units


def test_plane_serialization(sample_plane):
    serialized = serialize(sample_plane)
    deserialized = deserialize(serialized)

    assert deserialized.origin.x == sample_plane.origin.x
    assert deserialized.normal.z == sample_plane.normal.z
    assert deserialized.units == sample_plane.units


def test_plane_to_list():
    plane = Plane(
        origin=Point(x=1.0, y=2.0, z=3.0, units="m"),
        normal=Vector(x=0.0, y=0.0, z=1.0, units="m"),
        xdir=Vector(x=1.0, y=0.0, z=0.0, units="m"),
        ydir=Vector(x=0.0, y=1.0, z=0.0, units="m"),
        units="m"
    )
    coords = plane.to_list()
    # total_length, type, units_encoding + 12 coordinates
    assert len(coords) == 15
    assert coords[3:6] == [1.0, 2.0, 3.0]  # origin
    assert coords[6:9] == [0.0, 0.0, 1.0]  # normal
    assert coords[9:12] == [1.0, 0.0, 0.0]  # xdir
    assert coords[12:15] == [0.0, 1.0, 0.0]  # ydir


def test_plane_from_list():
    coords = [15, "Objects.Geometry.Plane", 3,  # header
              1.0, 2.0, 3.0,  # origin
              0.0, 0.0, 1.0,  # normal
              1.0, 0.0, 0.0,  # xdir
              0.0, 1.0, 0.0]  # ydir
    plane = Plane.from_list(coords)
    assert plane.origin.x == 1.0
    assert plane.origin.y == 2.0
    assert plane.origin.z == 3.0
    assert plane.normal.x == 0.0
    assert plane.normal.y == 0.0
    assert plane.normal.z == 1.0
    assert plane.xdir.x == 1.0
    assert plane.xdir.y == 0.0
    assert plane.xdir.z == 0.0
    assert plane.ydir.x == 0.0
    assert plane.ydir.y == 1.0
    assert plane.ydir.z == 0.0
    assert plane.units == "m"
