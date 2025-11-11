from typing import List, Tuple

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import Line, Point, Polycurve, Polyline
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_points() -> Tuple[Point, Point, Point]:
    return (
        Point(x=0.0, y=0.0, z=0.0, units=Units.m),
        Point(x=1.0, y=0.0, z=0.0, units=Units.m),
        Point(x=1.0, y=1.0, z=0.0, units=Units.m),
    )


@pytest.fixture
def sample_lines(sample_points: Tuple[Point, Point, Point]) -> List[Line]:
    p1, p2, p3 = sample_points
    return [
        Line(start=p1, end=p2, units=Units.m),
        Line(start=p2, end=p3, units=Units.m),
    ]


@pytest.fixture
def sample_polycurve(sample_lines: List[Line]) -> Polycurve:
    return Polycurve(segments=sample_lines, units=Units.m)


def test_polycurve_creation(sample_lines: List[Line]):
    polycurve = Polycurve(segments=sample_lines, units=Units.m)
    assert len(polycurve.segments) == 2
    assert polycurve.units == Units.m.value
    assert isinstance(polycurve.segments[0], Line)


def test_polycurve_is_closed(sample_points: Tuple[Point, Point, Point]):
    p1, p2, p3 = sample_points
    lines = [
        Line(start=p1, end=p2, units=Units.m),
        Line(start=p2, end=p3, units=Units.m),
        Line(start=p3, end=p1, units=Units.m),
    ]
    closed_polycurve = Polycurve(segments=lines, units=Units.m)
    assert closed_polycurve.is_closed()


def test_polycurve_not_closed(sample_polycurve: Polycurve):
    assert not sample_polycurve.is_closed()


@pytest.mark.parametrize("expected_length", [2.0])
def test_polycurve_length(sample_polycurve: Polycurve, expected_length: float):
    sample_polycurve.length = sample_polycurve.calculate_length()
    assert sample_polycurve.length == pytest.approx(expected_length)


@pytest.mark.parametrize(
    "points,expected_segments,expected_closed",
    [
        ([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0], 2, False),
        (
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            4,
            True,
        ),
    ],
)
def test_polycurve_from_polyline(
    points: List[float], expected_segments: int, expected_closed: bool
):
    polyline = Polyline(value=points, units=Units.m)
    polycurve = Polycurve.from_polyline(polyline)

    assert len(polycurve.segments) == expected_segments
    assert polycurve.units == Units.m.value
    assert isinstance(polycurve.segments[0], Line)
    assert polycurve.is_closed() == expected_closed


def test_polycurve_serialization(sample_polycurve: Polycurve):
    serialized = serialize(sample_polycurve)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Polycurve)
    assert len(deserialized.segments) == len(sample_polycurve.segments)
    assert deserialized.units == sample_polycurve.units

    expectedSegment = sample_polycurve.segments[0]
    segment = deserialized.segments[0]
    assert isinstance(expectedSegment, Line)
    assert isinstance(segment, Line)

    assert segment.start.x == expectedSegment.start.x
    assert segment.start.y == expectedSegment.start.y
    assert segment.start.z == expectedSegment.start.z
    assert segment.end.x == expectedSegment.end.x
    assert segment.end.y == expectedSegment.end.y
    assert segment.end.z == expectedSegment.end.z


def test_polycurve_empty():
    polycurve = Polycurve(segments=[], units=Units.m)
    assert not polycurve.is_closed()
    assert polycurve.calculate_length() == 0.0


def test_polycurve_invalid_segment():
    with pytest.raises(SpeckleException):
        Polycurve(segments=["not a curve"], units=Units.m)
