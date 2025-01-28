import math
import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Ellipse, Plane, Point, Vector
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def sample_plane():
    origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

    return Plane(origin=origin, normal=normal, xdir=xdir, ydir=ydir, units=Units.m)


@pytest.fixture
def sample_ellipse(sample_plane):
    return Ellipse(
        plane=sample_plane,
        first_radius=2.0,
        second_radius=1.0,
        units=Units.m
    )


def test_ellipse_creation(sample_plane):
    ellipse = Ellipse(
        plane=sample_plane,
        first_radius=2.0,
        second_radius=1.0,
        units=Units.m
    )

    assert ellipse.plane == sample_plane
    assert ellipse.first_radius == 2.0
    assert ellipse.second_radius == 1.0
    assert ellipse.units == Units.m.value


def test_ellipse_domain(sample_ellipse):
    assert isinstance(sample_ellipse.domain, Interval)
    assert sample_ellipse.domain.start == 0.0
    assert sample_ellipse.domain.end == 1.0


def test_ellipse_area(sample_ellipse):
    area = math.pi * sample_ellipse.first_radius * sample_ellipse.second_radius
    sample_ellipse.area = area
    assert sample_ellipse.area == pytest.approx(area)


def test_ellipse_units(sample_plane):
    ellipse = Ellipse(
        plane=sample_plane,
        first_radius=2.0,
        second_radius=1.0,
        units=Units.m
    )

    assert ellipse.units == Units.m.value

    ellipse.units = "mm"
    assert ellipse.units == "mm"


def test_ellipse_invalid_construction(sample_plane):
    with pytest.raises(Exception):
        Ellipse(
            plane="not a plane",
            first_radius=2.0,
            second_radius=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        Ellipse(
            plane=sample_plane,
            first_radius="not a number",
            second_radius=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        Ellipse(
            plane=sample_plane,
            first_radius=2.0,
            second_radius="not a number",
            units=Units.m
        )


def test_ellipse_serialization(sample_ellipse):
    serialized = serialize(sample_ellipse)
    deserialized = deserialize(serialized)

    assert deserialized.plane.origin.x == sample_ellipse.plane.origin.x
    assert deserialized.plane.origin.y == sample_ellipse.plane.origin.y
    assert deserialized.plane.origin.z == sample_ellipse.plane.origin.z

    assert deserialized.first_radius == sample_ellipse.first_radius
    assert deserialized.second_radius == sample_ellipse.second_radius
    assert deserialized.units == sample_ellipse.units
