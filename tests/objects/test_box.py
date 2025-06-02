# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Box, Plane, Point, Vector
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
def sample_intervals():
    return (
        Interval(start=0.0, end=1.0),
        Interval(start=0.0, end=1.0),
        Interval(start=0.0, end=1.0),
    )


@pytest.fixture
def sample_box(sample_plane, sample_intervals):
    xsize, ysize, zsize = sample_intervals
    return Box(
        basePlane=sample_plane, xSize=xsize, ySize=ysize, zSize=zsize, units=Units.m
    )


def test_box_creation(sample_plane, sample_intervals):
    xsize, ysize, zsize = sample_intervals
    box = Box(
        basePlane=sample_plane, xSize=xsize, ySize=ysize, zSize=zsize, units=Units.m
    )

    assert box.basePlane == sample_plane
    assert box.xSize == xsize
    assert box.ySize == ysize
    assert box.zSize == zsize
    assert box.units == Units.m.value


@pytest.mark.parametrize("expected_area", [6.0])  # 6 faces, each 1x1
def test_box_area(sample_box, expected_area):
    sample_box.area = sample_box.area
    assert sample_box.area == pytest.approx(expected_area)


@pytest.mark.parametrize("expected_volume", [1.0])  # 1x1x1 cube
def test_box_volume(sample_box, expected_volume):
    sample_box.volume = sample_box.volume
    assert sample_box.volume == pytest.approx(expected_volume)


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_box_units(sample_plane, sample_intervals, new_units):
    xsize, ysize, zsize = sample_intervals
    box = Box(
        basePlane=sample_plane, xSize=xsize, ySize=ysize, zSize=zsize, units=Units.m
    )
    assert box.units == Units.m.value
    box.units = new_units
    assert box.units == new_units


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "basePlane",
            {"basePlane": "not a plane", "xSize": None, "ySize": None, "zSize": None},
            "Cannot set 'Box.basePlane':it expects type '<class 'specklepy.objects.geometry.plane.Plane'>',but received type 'str'",
        ),
        (
            "xSize",
            {
                "basePlane": None,
                "xSize": "not an interval",
                "ySize": None,
                "zSize": None,
            },
            "Cannot set 'Box.xSize':it expects type '<class 'specklepy.objects.primitive.Interval'>',but received type 'str'",
        ),
    ],
)
def test_box_inval(
    sample_plane, sample_intervals, invalid_param, test_params, error_msg
):
    xsize, ysize, zsize = sample_intervals

    if invalid_param != "basePlane":
        test_params["basePlane"] = sample_plane
    if invalid_param != "xSize":
        test_params["xSize"] = xsize
    if invalid_param != "ySize":
        test_params["ySize"] = ysize
    if invalid_param != "zSize":
        test_params["zSize"] = zsize

    with pytest.raises(SpeckleException) as exc_info:
        Box(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


def test_box_serialization(sample_box):
    serialized = serialize(sample_box)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Box)
    assert deserialized.basePlane.origin.x == sample_box.basePlane.origin.x
    assert deserialized.basePlane.origin.y == sample_box.basePlane.origin.y
    assert deserialized.basePlane.origin.z == sample_box.basePlane.origin.z

    assert deserialized.xSize.start == sample_box.xSize.start
    assert deserialized.xSize.end == sample_box.xSize.end
    assert deserialized.ySize.start == sample_box.ySize.start
    assert deserialized.ySize.end == sample_box.ySize.end
    assert deserialized.zSize.start == sample_box.zSize.start
    assert deserialized.zSize.end == sample_box.zSize.end

    assert deserialized.units == sample_box.units
