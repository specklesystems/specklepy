from typing import Any, Tuple

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Plane, Point, Spiral, Vector
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_points() -> Tuple[Point, Point]:
    return (
        Point(x=0.0, y=0.0, z=0.0, units=Units.m),
        Point(x=0.0, y=0.0, z=2.0, units=Units.m),
    )


@pytest.fixture
def sample_plane() -> Plane:
    origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
    ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)
    return Plane(origin=origin, normal=normal, xdir=xdir, ydir=ydir, units=Units.m)


@pytest.fixture
def sample_spiral(sample_points: Tuple[Point, Point], sample_plane: Plane) -> Spiral:
    start, end = sample_points
    pitch_axis = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    return Spiral(
        start_point=start,
        end_point=end,
        plane=sample_plane,
        turns=2.0,
        pitch=1.0,
        pitch_axis=pitch_axis,
        units=Units.m,
    )


@pytest.mark.parametrize("units", [Units.m])
def test_spiral_creation(
    sample_points: Tuple[Point, Point], sample_plane: Plane, units: Units
):
    start, end = sample_points
    pitch_axis = Vector(x=0.0, y=0.0, z=1.0, units=units)
    spiral = Spiral(
        start_point=start,
        end_point=end,
        plane=sample_plane,
        turns=2.0,
        pitch=1.0,
        pitch_axis=pitch_axis,
        units=units,
    )

    assert spiral.start_point == start
    assert spiral.end_point == end
    assert spiral.plane == sample_plane
    assert spiral.turns == 2.0
    assert spiral.pitch == 1.0
    assert spiral.pitch_axis == pitch_axis
    assert spiral.units == units.value


@pytest.mark.parametrize(
    "invalid_param,invalid_value",
    [
        ("start_point", "not a point"),
        ("end_point", "not a point"),
        ("plane", "not a plane"),
        ("turns", "not a number"),
    ],
)
def test_spiral_invalid_construction(
    sample_points: Tuple[Point, Point],
    sample_plane: Plane,
    invalid_param: str,
    invalid_value: Any,
):
    start, end = sample_points
    pitch_axis = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
    valid_params = {
        "start_point": start,
        "end_point": end,
        "plane": sample_plane,
        "turns": 2.0,
        "pitch": 1.0,
        "pitch_axis": pitch_axis,
        "units": Units.m,
    }
    valid_params[invalid_param] = invalid_value

    with pytest.raises(SpeckleException):
        Spiral(**valid_params)


@pytest.mark.parametrize("test_value", [10.0])
def test_spiral_length(sample_spiral: Spiral, test_value: float):
    sample_spiral.length = test_value
    assert sample_spiral.length == test_value


@pytest.mark.parametrize("test_value", [15.0])
def test_spiral_area(sample_spiral: Spiral, test_value: float):
    sample_spiral.area = test_value
    assert sample_spiral.area == test_value


def test_spiral_serialization(sample_spiral: Spiral):
    serialized = serialize(sample_spiral)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Spiral)
    assert deserialized.start_point.x == sample_spiral.start_point.x
    assert deserialized.start_point.y == sample_spiral.start_point.y
    assert deserialized.start_point.z == sample_spiral.start_point.z
    assert deserialized.end_point.x == sample_spiral.end_point.x
    assert deserialized.end_point.y == sample_spiral.end_point.y
    assert deserialized.end_point.z == sample_spiral.end_point.z
    assert deserialized.plane.origin.x == sample_spiral.plane.origin.x
    assert deserialized.plane.origin.y == sample_spiral.plane.origin.y
    assert deserialized.plane.origin.z == sample_spiral.plane.origin.z
    assert deserialized.turns == sample_spiral.turns
    assert deserialized.pitch == sample_spiral.pitch
    assert deserialized.pitch_axis.x == sample_spiral.pitch_axis.x
    assert deserialized.pitch_axis.y == sample_spiral.pitch_axis.y
    assert deserialized.pitch_axis.z == sample_spiral.pitch_axis.z
    assert deserialized.units == sample_spiral.units
