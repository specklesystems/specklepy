# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import math

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Arc, Plane, Point, Vector
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def sample_points():
    start = Point(x=1.0, y=0.0, z=0.0, units=Units.m)
    mid = Point(x=0.0, y=1.0, z=0.0, units=Units.m)
    end = Point(x=-1.0, y=0.0, z=0.0, units=Units.m)

    return start, mid, end


@pytest.fixture
def sample_plane():
    origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)

    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)

    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)

    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

    plane = Plane(origin=origin, normal=normal, xdir=xdir, ydir=ydir, units=Units.m)

    return plane


@pytest.fixture
def sample_arc(sample_points, sample_plane):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane, startPoint=start, midPoint=mid, endPoint=end, units=Units.m
    )

    return arc


def test_arc_creation(sample_points, sample_plane):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane, startPoint=start, midPoint=mid, endPoint=end, units=Units.m
    )

    assert arc.startPoint == start
    assert arc.midPoint == mid
    assert arc.endPoint == end
    assert arc.plane == sample_plane
    assert arc.units == Units.m.value


def test_arc_domain(sample_arc):
    assert isinstance(sample_arc.domain, Interval)
    assert sample_arc.domain.start == 0.0
    assert sample_arc.domain.end == 1.0


def test_arc_radius(sample_arc):
    assert sample_arc.radius == pytest.approx(1.0)


def test_arc_length(sample_arc):
    assert sample_arc.length == pytest.approx(math.pi)


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "plane",
            {
                "plane": "not a plane",
                "startPoint": None,
                "midPoint": None,
                "endPoint": None,
            },
            "Cannot set 'Arc.plane':it expects type '<class 'specklepy.objects.geometry.plane.Plane'>',but received type 'str'",
        ),
        (
            "startPoint",
            {
                "plane": None,
                "startPoint": "not a point",
                "midPoint": None,
                "endPoint": None,
            },
            "Cannot set 'Arc.startPoint':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
        (
            "midPoint",
            {
                "plane": None,
                "startPoint": None,
                "midPoint": "not a point",
                "endPoint": None,
            },
            "Cannot set 'Arc.midPoint':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
        (
            "endPoint",
            {
                "plane": None,
                "startPoint": None,
                "midPoint": None,
                "endPoint": "not a point",
            },
            "Cannot set 'Arc.endPoint':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
    ],
)
def test_arc_inval(sample_points, sample_plane, invalid_param, test_params, error_msg):
    start, mid, end = sample_points

    if invalid_param != "plane":
        test_params["plane"] = sample_plane
    if invalid_param != "startPoint":
        test_params["startPoint"] = start
    if invalid_param != "midPoint":
        test_params["midPoint"] = mid
    if invalid_param != "endPoint":
        test_params["endPoint"] = end

    with pytest.raises(SpeckleException) as exc_info:
        Arc(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_arc_units(sample_points, sample_plane, new_units):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane, startPoint=start, midPoint=mid, endPoint=end, units=Units.m
    )
    assert arc.units == Units.m.value
    arc.units = new_units
    assert arc.units == new_units


def test_arc_serialization(sample_arc):
    serialized = serialize(sample_arc)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Arc)
    assert deserialized.startPoint.x == sample_arc.startPoint.x
    assert deserialized.startPoint.y == sample_arc.startPoint.y
    assert deserialized.startPoint.z == sample_arc.startPoint.z

    assert deserialized.midPoint.x == sample_arc.midPoint.x
    assert deserialized.midPoint.y == sample_arc.midPoint.y
    assert deserialized.midPoint.z == sample_arc.midPoint.z

    assert deserialized.endPoint.x == sample_arc.endPoint.x
    assert deserialized.endPoint.y == sample_arc.endPoint.y
    assert deserialized.endPoint.z == sample_arc.endPoint.z

    assert deserialized.plane.origin.x == sample_arc.plane.origin.x
    assert deserialized.plane.origin.y == sample_arc.plane.origin.y
    assert deserialized.plane.origin.z == sample_arc.plane.origin.z

    assert deserialized.units == sample_arc.units
