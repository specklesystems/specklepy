import pytest

from specklepy.core.api.operations import deserialize, serialize
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
    line = Line(start=start, end=end, units=Units.m)
    return line


def test_line_creation(sample_points):

    start, end = sample_points
    line = Line(start=start, end=end, units=Units.m)

    assert line.start == start
    assert line.end == end
    assert line.units == Units.m.value


def test_line_domain(sample_line):

    # Domain should be automatically initialized to unit interval by ICurve
    assert isinstance(sample_line.domain, Interval)
    assert sample_line.domain.start == 0.0
    assert sample_line.domain.end == 1.0


def test_line_length(sample_line):

    sample_line.length = sample_line.calculate_length()
    assert sample_line.length == 5.0


def test_line_units(sample_points):

    start, end = sample_points
    line = Line(start=start, end=end, units=Units.m)

    assert line.units == Units.m.value

    # Test setting units with string
    line.units = "mm"
    assert line.units == "mm"


def test_line_serialization(sample_line):

    serialized = serialize(sample_line)
    deserialized = deserialize(serialized)

    assert deserialized.start.x == sample_line.start.x
    assert deserialized.start.y == sample_line.start.y
    assert deserialized.start.z == sample_line.start.z
    assert deserialized.end.x == sample_line.end.x
    assert deserialized.end.y == sample_line.end.y
    assert deserialized.end.z == sample_line.end.z
    assert deserialized.units == sample_line.units
    assert deserialized.domain.start == sample_line.domain.start
    assert deserialized.domain.end == sample_line.domain.end


def test_line_invalid_construction():
    """Test error cases"""
    p1 = Point(x=0.0, y=0.0, z=0.0, units=Units.m)

    # Test with invalid start point
    with pytest.raises(Exception):
        Line(start="not a point", end=p1)

    # Test with invalid end point
    with pytest.raises(Exception):
        Line(start=p1, end="not a point")
