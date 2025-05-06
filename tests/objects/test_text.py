import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.annotation import AlignmentHorizontal, AlignmentVertical, Text
from specklepy.objects.geometry import Plane, Point, Vector
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_point() -> Point:
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
def sample_text(sample_point: Point) -> Text:
    return Text(value="text", origin=sample_point, height=0.5, units=Units.m)


@pytest.fixture
def sample_text_all_properties(sample_point: Point, sample_plane: Plane) -> Text:
    return Text(
        value="text",
        origin=sample_point,
        height=0.5,
        alignmentH=AlignmentHorizontal.Center,
        alignmentV=AlignmentVertical.Center,
        plane=sample_plane,
        maxWidth=20,
        units=Units.m,
    )


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


def test_point_serialization(sample_text_all_properties: Text):
    serialized = serialize(sample_text_all_properties)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Text)
    assert deserialized.value == sample_text_all_properties.value
    assert deserialized.origin.x == sample_text_all_properties.origin.x
    assert deserialized.origin.y == sample_text_all_properties.origin.y
    assert deserialized.origin.z == sample_text_all_properties.origin.z
    assert deserialized.height == sample_text_all_properties.height
    assert deserialized.alignmentH == sample_text_all_properties.alignmentH
    assert deserialized.alignmentV == sample_text_all_properties.alignmentV
    assert deserialized.plane.origin.x == sample_text_all_properties.plane.origin.x
    assert deserialized.plane.origin.y == sample_text_all_properties.plane.origin.y
    assert deserialized.plane.origin.z == sample_text_all_properties.plane.origin.z
    assert deserialized.plane.normal.x == sample_text_all_properties.plane.normal.x
    assert deserialized.plane.normal.y == sample_text_all_properties.plane.normal.y
    assert deserialized.plane.normal.z == sample_text_all_properties.plane.normal.z
    assert deserialized.maxWidth == sample_text_all_properties.maxWidth
    assert deserialized.units == sample_text_all_properties.units
