import math
import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Circle, Plane, Point, Vector
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def sample_plane():
    origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

    plane = Plane(
        origin=origin,
        normal=normal,
        xdir=xdir,
        ydir=ydir,
        units=Units.m
    )
    return plane


@pytest.fixture
def sample_center():
    return Point(x=0.0, y=0.0, z=0.0, units=Units.m)


@pytest.fixture
def sample_circle(sample_plane, sample_center):
    circle = Circle(
        plane=sample_plane,
        center=sample_center,
        radius=1.0,
        units=Units.m
    )
    return circle


def test_circle_creation(sample_plane, sample_center):
    circle = Circle(
        plane=sample_plane,
        center=sample_center,
        radius=1.0,
        units=Units.m
    )

    assert circle.plane == sample_plane
    assert circle.center == sample_center
    assert circle.radius == 1.0
    assert circle.units == Units.m.value


def test_circle_domain(sample_circle):
    # domain should be automatically initialized to unit interval by ICurve
    assert isinstance(sample_circle.domain, Interval)
    assert sample_circle.domain.start == 0.0
    assert sample_circle.domain.end == 1.0


def test_circle_length(sample_circle):
    # circumference of circle with radius 1.0 should be 2π
    assert sample_circle.length == pytest.approx(2 * math.pi)


def test_circle_area(sample_circle):
    # area of circle with radius 1.0 should be π
    assert sample_circle.area == pytest.approx(math.pi)


def test_circle_units(sample_plane, sample_center):
    circle = Circle(
        plane=sample_plane,
        center=sample_center,
        radius=1.0,
        units=Units.m
    )

    assert circle.units == Units.m.value

    circle.units = "mm"
    assert circle.units == "mm"


def test_circle_invalid_construction(sample_plane, sample_center):
    with pytest.raises(Exception):
        Circle(
            plane="not a plane",
            center=sample_center,
            radius=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        Circle(
            plane=sample_plane,
            center="not a point",
            radius=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        Circle(
            plane=sample_plane,
            center=sample_center,
            radius="not a number",
            units=Units.m
        )


def test_circle_serialization(sample_circle):
    serialized = serialize(sample_circle)
    deserialized = deserialize(serialized)

    assert deserialized.plane.origin.x == sample_circle.plane.origin.x
    assert deserialized.plane.origin.y == sample_circle.plane.origin.y
    assert deserialized.plane.origin.z == sample_circle.plane.origin.z

    assert deserialized.plane.normal.x == sample_circle.plane.normal.x
    assert deserialized.plane.normal.y == sample_circle.plane.normal.y
    assert deserialized.plane.normal.z == sample_circle.plane.normal.z

    assert deserialized.center.x == sample_circle.center.x
    assert deserialized.center.y == sample_circle.center.y
    assert deserialized.center.z == sample_circle.center.z

    assert deserialized.radius == sample_circle.radius
    assert deserialized.units == sample_circle.units
