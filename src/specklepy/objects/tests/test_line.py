import pytest
from specklepy.objects.geometry.line import Line
from specklepy.objects.geometry.point import Point
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.objects.primitive import Interval
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def sample_line():
    p1 = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    p2 = Point(x=3.0, y=4.0, z=0.0, units=Units.m)
    return Line(start=p1, end=p2, units=Units.m, domain=Interval(start=0.0, end=1.0))


def test_line_creation(sample_line):
    assert sample_line.start.x == 0.0
    assert sample_line.end.x == 3.0
    assert sample_line.units == Units.m.value


def test_line_length(sample_line):
    assert sample_line.length == 5.0


def test_line_transformation(sample_line):
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = sample_line.transform_to(transform)
    assert success is True
    assert transformed.start.x == 1.0
    assert transformed.end.x == 7.0
    assert transformed.units == sample_line.units


def test_line_serialization(sample_line):
    serialized = serialize(sample_line)
    deserialized = deserialize(serialized)

    assert deserialized.start.x == sample_line.start.x
    assert deserialized.end.x == sample_line.end.x
    assert deserialized.units == sample_line.units


def test_line_from_list():
    coords = [11, "Objects.Geometry.Line", 3,
              1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.0, 1.0]
    line = Line.from_list(coords, "m")
    assert line.start.x == 1.0
    assert line.start.y == 2.0
    assert line.start.z == 3.0
    assert line.end.x == 4.0
    assert line.end.y == 5.0
    assert line.end.z == 6.0
    assert line.domain.start == 0.0
    assert line.domain.end == 1.0
    assert line.units == "m"


def test_line_from_coords():
    line = Line.from_coords(0.0, 0.0, 0.0, 3.0, 4.0, 0.0, Units.m.value)
    assert line.start.x == 0.0
    assert line.end.x == 3.0
    assert line.units == Units.m.value
