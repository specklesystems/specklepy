import math

import pytest

from specklepy.core.api.operations import deserialize, serialize
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

    plane = Plane(origin=origin, normal=normal,
                  xdir=xdir, ydir=ydir, units=Units.m)

    return plane


@pytest.fixture
def sample_arc(sample_points, sample_plane):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane,
        startPoint=start,
        midPoint=mid,
        endPoint=end,
        units=Units.m
    )

    return arc


def test_arc_creation(sample_points, sample_plane):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane,
        startPoint=start,
        midPoint=mid,
        endPoint=end,
        units=Units.m
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


def test_arc_units(sample_points, sample_plane):
    start, mid, end = sample_points
    arc = Arc(
        plane=sample_plane,
        startPoint=start,
        midPoint=mid,
        endPoint=end,
        units=Units.m
    )

    assert arc.units == Units.m.value

    arc.units = "mm"
    assert arc.units == "mm"


def test_arc_invalid_construction(sample_points, sample_plane):
    start, mid, end = sample_points

    with pytest.raises(Exception):
        Arc(
            plane="not a plane",
            startPoint=start,
            midPoint=mid,
            endPoint=end,
            units=Units.m
        )

    with pytest.raises(Exception):
        Arc(
            plane=sample_plane,
            startPoint="not a point",
            midPoint=mid,
            endPoint=end,
            units=Units.m
        )

    with pytest.raises(Exception):
        Arc(
            plane=sample_plane,
            startPoint=start,
            midPoint="not a point",
            endPoint=end,
            units=Units.m
        )

    with pytest.raises(Exception):
        Arc(
            plane=sample_plane,
            startPoint=start,
            midPoint=mid,
            endPoint="not a point",
            units=Units.m
        )


def test_arc_serialization(sample_arc):
    serialized = serialize(sample_arc)
    deserialized = deserialize(serialized)

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
