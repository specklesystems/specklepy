# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import math

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Circle, Plane, Point, Vector
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
def sample_center():
    return Point(x=0.0, y=0.0, z=0.0, units=Units.m)


@pytest.fixture
def sample_circle(sample_plane, sample_center):
    return Circle(plane=sample_plane, center=sample_center, radius=1.0, units=Units.m)


def test_circle_creation(sample_plane, sample_center):
    circle = Circle(plane=sample_plane, center=sample_center, radius=1.0, units=Units.m)
    assert circle.plane == sample_plane
    assert circle.center == sample_center
    assert circle.radius == 1.0
    assert circle.units == Units.m.value


def test_circle_domain(sample_circle):
    assert isinstance(sample_circle.domain, Interval)
    assert sample_circle.domain.start == 0.0
    assert sample_circle.domain.end == 1.0


@pytest.mark.parametrize(
    "radius,expected_length", [(1.0, 2 * math.pi), (2.0, 4 * math.pi), (0.5, math.pi)]
)
def test_circle_length(sample_circle, radius, expected_length):
    sample_circle.radius = radius
    assert sample_circle.length == pytest.approx(expected_length)


@pytest.mark.parametrize(
    "radius,expected_area", [(1.0, math.pi), (2.0, 4 * math.pi), (0.5, math.pi * 0.25)]
)
def test_circle_area(sample_circle, radius, expected_area):
    sample_circle.radius = radius
    assert sample_circle.area == pytest.approx(expected_area)


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_circle_units(sample_plane, sample_center, new_units):
    circle = Circle(plane=sample_plane, center=sample_center, radius=1.0, units=Units.m)
    assert circle.units == Units.m.value
    circle.units = new_units
    assert circle.units == new_units


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "plane",
            {"plane": "not a plane", "center": None, "radius": 1.0},
            "Cannot set 'Circle.plane':it expects type '<class 'specklepy.objects.geometry.plane.Plane'>',but received type 'str'",
        ),
        (
            "center",
            {"plane": None, "center": "not a point", "radius": 1.0},
            "Cannot set 'Circle.center':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
        (
            "radius",
            {"plane": None, "center": None, "radius": "not a number"},
            "Cannot set 'Circle.radius':it expects type '<class 'float'>',but received type 'str'",
        ),
    ],
)
def test_circle_inval(
    sample_plane, sample_center, invalid_param, test_params, error_msg
):
    if invalid_param != "plane":
        test_params["plane"] = sample_plane
    if invalid_param != "center":
        test_params["center"] = sample_center

    with pytest.raises(SpeckleException) as exc_info:
        Circle(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


def test_circle_serialization(sample_circle):
    serialized = serialize(sample_circle)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Circle)
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
