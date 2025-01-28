import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Box, Plane, Point, Vector
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
def sample_box(sample_plane):
    # create a 1x1x1 meter cube
    xsize = Interval(start=0.0, end=1.0)
    ysize = Interval(start=0.0, end=1.0)
    zsize = Interval(start=0.0, end=1.0)

    box = Box(
        basePlane=sample_plane,
        xSize=xsize,
        ySize=ysize,
        zSize=zsize,
        units=Units.m
    )
    return box


def test_box_creation(sample_plane):
    xsize = Interval(start=0.0, end=1.0)
    ysize = Interval(start=0.0, end=1.0)
    zsize = Interval(start=0.0, end=1.0)

    box = Box(
        basePlane=sample_plane,
        xSize=xsize,
        ySize=ysize,
        zSize=zsize,
        units=Units.m
    )

    assert box.basePlane == sample_plane
    assert box.xSize == xsize
    assert box.ySize == ysize
    assert box.zSize == zsize
    assert box.units == Units.m.value


def test_box_area(sample_box):
    # for a 1x1x1 cube, surface area should be 6 square meters
    expected_area = 6.0  # 6 faces, each 1x1
    sample_box.area = sample_box.area
    assert sample_box.area == pytest.approx(expected_area)


def test_box_volume(sample_box):
    # for a 1x1x1 cube, volume should be 1 cubic meter
    expected_volume = 1.0
    sample_box.volume = sample_box.volume
    assert sample_box.volume == pytest.approx(expected_volume)


def test_box_units(sample_plane):
    box = Box(
        basePlane=sample_plane,
        xSize=Interval(start=0.0, end=1.0),
        ySize=Interval(start=0.0, end=1.0),
        zSize=Interval(start=0.0, end=1.0),
        units=Units.m
    )

    assert box.units == Units.m.value

    box.units = "mm"
    assert box.units == "mm"


def test_box_invalid_construction(sample_plane):
    with pytest.raises(Exception):
        Box(
            basePlane="not a plane",
            xSize=Interval(start=0.0, end=1.0),
            ySize=Interval(start=0.0, end=1.0),
            zSize=Interval(start=0.0, end=1.0),
            units=Units.m
        )

    with pytest.raises(Exception):
        Box(
            basePlane=sample_plane,
            xSize="not an interval",
            ySize=Interval(start=0.0, end=1.0),
            zSize=Interval(start=0.0, end=1.0),
            units=Units.m
        )


def test_box_serialization(sample_box):
    serialized = serialize(sample_box)
    deserialized = deserialize(serialized)

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
