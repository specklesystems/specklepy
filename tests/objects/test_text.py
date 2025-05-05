import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.annotation import AlignmentHorizontal, AlignmentVertical, Text
from specklepy.objects.geometry import Vector, Point, Plane
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_point():
    return Point(x=0.0, y=0.0, z=0.0, units=Units.m)


@pytest.fixture
def sample_plane(sample_point: Point) -> Plane:
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)
    return Plane(
        origin=sample_point, normal=normal, xdir=xdir, ydir=ydir, units=Units.m
    )


@pytest.fixture
def sample_text(sample_point: Point) -> Plane:
    return Text(value="text", origin=sample_point, height=0.5, units=Units.m)


def test_text_creation_minimal(sample_point: Point):
    text_value = "text"

    text_obj = Text(value=text_value, origin=sample_point, height=0.5, units=Units.m)
    assert text_obj.value == text_value
    assert text_obj.origin == sample_point
    assert text_obj.height == 0.5
    assert text_obj.alignmentH == AlignmentHorizontal.Left
    assert text_obj.alignmentV == AlignmentVertical.Top
    assert text_obj.plane is None
    assert text_obj.maxWidth is None
    assert text_obj.units == Units.m.value


def test_text_creation_extended(sample_point: Point, sample_plane: Plane):
    text_value = "text"
    max_width = 20

    text_obj = Text(
        value=text_value,
        origin=sample_point,
        height=0.5,
        alignmentH=AlignmentHorizontal.Center,
        alignmentV=AlignmentVertical.Center,
        plane=sample_plane,
        maxWidth=max_width,
        units=Units.m,
    )
    assert text_obj.value == text_value
    assert text_obj.origin == sample_point
    assert text_obj.height == 0.5
    assert text_obj.alignmentH == AlignmentHorizontal.Center
    assert text_obj.alignmentV == AlignmentVertical.Center
    assert text_obj.plane == sample_plane
    assert text_obj.maxWidth == max_width
    assert text_obj.units == Units.m.value


def test_point_serialization(sample_text: Text):
    serialized = serialize(sample_text)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Text)
    assert deserialized.value == sample_text.value
    assert deserialized.origin == sample_text.origin
    assert deserialized.height == sample_text.height
    assert deserialized.alignmentH == sample_text.alignmentH
    assert deserialized.alignmentV == sample_text.alignmentV
    assert deserialized.plane == sample_text.plane
    assert deserialized.maxWidth == sample_text.maxWidth
    assert deserialized.units == sample_text.units
