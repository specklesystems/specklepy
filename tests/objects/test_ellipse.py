# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import math

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
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
        plane=sample_plane, first_radius=2.0, second_radius=1.0, units=Units.m
    )


def test_ellipse_creation(sample_plane):
    ellipse = Ellipse(
        plane=sample_plane, first_radius=2.0, second_radius=1.0, units=Units.m
    )

    assert ellipse.plane == sample_plane
    assert ellipse.first_radius == 2.0
    assert ellipse.second_radius == 1.0
    assert ellipse.units == Units.m.value


def test_ellipse_domain(sample_ellipse):
    assert isinstance(sample_ellipse.domain, Interval)
    assert sample_ellipse.domain.start == 0.0
    assert sample_ellipse.domain.end == 1.0


@pytest.mark.parametrize(
    "area_value",
    [
        10.0,
        math.pi * 2.0,  # area for circle with radius 2
        0.0,
    ],
)
def test_ellipse_area(sample_ellipse, area_value):
    sample_ellipse.area = area_value
    assert sample_ellipse.area == pytest.approx(area_value)


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_ellipse_units(sample_plane, new_units):
    ellipse = Ellipse(
        plane=sample_plane, first_radius=2.0, second_radius=1.0, units=Units.m
    )
    assert ellipse.units == Units.m.value

    ellipse.units = new_units
    assert ellipse.units == new_units


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "plane",
            {"plane": "not a plane", "first_radius": 2.0, "second_radius": 1.0},
            "Cannot set 'Ellipse.plane':it expects type '<class 'specklepy.objects.geometry.plane.Plane'>',but received type 'str'",
        ),
        (
            "first_radius",
            {"plane": None, "first_radius": "not a number", "second_radius": 1.0},
            "Cannot set 'Ellipse.first_radius':it expects type '<class 'float'>',but received type 'str'",
        ),
        (
            "second_radius",
            {"plane": None, "first_radius": 2.0, "second_radius": "not number"},
            "Cannot set 'Ellipse.second_radius':it expects type '<class 'float'>',but received type 'str'",
        ),
    ],
)
def test_ellipse_invalid(sample_plane, invalid_param, test_params, error_msg):
    if invalid_param != "plane":
        test_params["plane"] = sample_plane

    with pytest.raises(SpeckleException) as exc_info:
        Ellipse(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


def test_ellipse_serialization(sample_ellipse):
    serialized = serialize(sample_ellipse)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Ellipse)
    assert deserialized.plane.origin.x == sample_ellipse.plane.origin.x
    assert deserialized.plane.origin.y == sample_ellipse.plane.origin.y
    assert deserialized.plane.origin.z == sample_ellipse.plane.origin.z

    assert deserialized.first_radius == sample_ellipse.first_radius
    assert deserialized.second_radius == sample_ellipse.second_radius
    assert deserialized.units == sample_ellipse.units
