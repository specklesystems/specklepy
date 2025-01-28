import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Line, Point, Polycurve, Polyline
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_points():
    p1 = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
    p2 = Point(x=1.0, y=0.0, z=0.0, units=Units.m)
    p3 = Point(x=1.0, y=1.0, z=0.0, units=Units.m)
    return p1, p2, p3


@pytest.fixture
def sample_lines(sample_points):
    p1, p2, p3 = sample_points
    line1 = Line(start=p1, end=p2, units=Units.m)
    line2 = Line(start=p2, end=p3, units=Units.m)
    return [line1, line2]


@pytest.fixture
def sample_polycurve(sample_lines):
    return Polycurve(segments=sample_lines, units=Units.m)


def test_polycurve_creation(sample_lines):
    polycurve = Polycurve(segments=sample_lines, units=Units.m)
    assert len(polycurve.segments) == 2
    assert polycurve.units == Units.m.value
    assert isinstance(polycurve.segments[0], Line)


def test_polycurve_is_closed(sample_points):
    p1, p2, p3 = sample_points
    lines = [
        Line(start=p1, end=p2, units=Units.m),
        Line(start=p2, end=p3, units=Units.m),
        Line(start=p3, end=p1, units=Units.m)
    ]
    closed_polycurve = Polycurve(segments=lines, units=Units.m)
    assert closed_polycurve.is_closed()


def test_polycurve_not_closed(sample_polycurve):
    assert not sample_polycurve.is_closed()


def test_polycurve_length(sample_polycurve):
    sample_polycurve.length = sample_polycurve.calculate_length()
    assert sample_polycurve.length == pytest.approx(2.0)


def test_polycurve_from_polyline():
    points = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0]
    polyline = Polyline(value=points, units=Units.m)
    polycurve = Polycurve.from_polyline(polyline)

    assert len(polycurve.segments) == 2
    assert polycurve.units == Units.m.value
    assert isinstance(polycurve.segments[0], Line)
    assert not polycurve.is_closed()


def test_polycurve_from_closed_polyline():
    points = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    polyline = Polyline(value=points, units=Units.m)
    polycurve = Polycurve.from_polyline(polyline)

    assert len(polycurve.segments) == 4
    assert polycurve.is_closed()


def test_polycurve_serialization(sample_polycurve):
    serialized = serialize(sample_polycurve)
    deserialized = deserialize(serialized)

    assert len(deserialized.segments) == len(sample_polycurve.segments)
    assert deserialized.units == sample_polycurve.units

    # verify first segment points
    assert deserialized.segments[0].start.x == sample_polycurve.segments[0].start.x
    assert deserialized.segments[0].start.y == sample_polycurve.segments[0].start.y
    assert deserialized.segments[0].start.z == sample_polycurve.segments[0].start.z
    assert deserialized.segments[0].end.x == sample_polycurve.segments[0].end.x
    assert deserialized.segments[0].end.y == sample_polycurve.segments[0].end.y
    assert deserialized.segments[0].end.z == sample_polycurve.segments[0].end.z


def test_polycurve_empty():
    polycurve = Polycurve(segments=[], units=Units.m)
    assert not polycurve.is_closed()
    assert polycurve.calculate_length() == 0.0


def test_polycurve_invalid_segment():
    with pytest.raises(Exception):
        Polycurve(segments=["not a curve"], units=Units.m)
