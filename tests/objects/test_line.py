# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Line, Point
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def sample_points():
    p1 = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    p2 = Point(x=3.0, y=4.0, z=0.0, units=Units.m)
    return p1, p2


@pytest.fixture
def sample_line(sample_points):
    start, end = sample_points
    return Line(start=start, end=end, units=Units.m)


def test_line_creation(sample_points):
    start, end = sample_points
    line = Line(start=start, end=end, units=Units.m)
    assert line.start == start
    assert line.end == end
    assert line.units == Units.m.value


def test_line_domain(sample_line):
    assert isinstance(sample_line.domain, Interval)
    assert sample_line.domain.start == 0.0
    assert sample_line.domain.end == 1.0


@pytest.mark.parametrize("expected_length", [5.0])
def test_line_length(sample_line, expected_length):
    assert sample_line.length == expected_length


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_line_units(sample_points, new_units):
    start, end = sample_points
    line = Line(start=start, end=end, units=Units.m)
    assert line.units == Units.m.value
    line.units = new_units
    assert line.units == new_units


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "start",
            {"start": "not a point", "end": None},
            "Cannot set 'Line.start':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
        (
            "end",
            {"start": None, "end": "not a point"},
            "Cannot set 'Line.end':it expects type '<class 'specklepy.objects.geometry.point.Point'>',but received type 'str'",
        ),
    ],
)
def test_line_invalid(sample_points, invalid_param, test_params, error_msg):
    start, end = sample_points
    if invalid_param != "start":
        test_params["start"] = start
    if invalid_param != "end":
        test_params["end"] = end

    with pytest.raises(SpeckleException) as exc_info:
        Line(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


def test_line_serialization(sample_line):
    serialized = serialize(sample_line)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Line)
    assert deserialized.start.x == sample_line.start.x
    assert deserialized.start.y == sample_line.start.y
    assert deserialized.start.z == sample_line.start.z
    assert deserialized.end.x == sample_line.end.x
    assert deserialized.end.y == sample_line.end.y
    assert deserialized.end.z == sample_line.end.z
    assert deserialized.units == sample_line.units
    assert deserialized.domain.start == sample_line.domain.start
    assert deserialized.domain.end == sample_line.domain.end
