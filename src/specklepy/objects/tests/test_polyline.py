import pytest
from specklepy.objects.geometry.polyline import Polyline
from specklepy.objects.geometry.point import Point
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.objects.primitive import Interval
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def square_vertices():
    return [
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0
    ]


@pytest.fixture
def sample_polyline(square_vertices):
    return Polyline(
        value=square_vertices,
        closed=True,
        units=Units.m,
        domain=Interval(start=0.0, end=1.0)
    )


def test_polyline_creation(square_vertices):
    polyline = Polyline(
        value=square_vertices,
        closed=True,
        units=Units.m,
        domain=Interval(start=0.0, end=1.0)
    )

    assert len(polyline.value) == 12
    assert polyline.closed is True
    assert polyline.units == Units.m.value
    assert isinstance(polyline.domain, Interval)
    assert polyline.domain.start == 0.0
    assert polyline.domain.end == 1.0


def test_polyline_get_points(sample_polyline):
    points = sample_polyline.get_points()

    assert len(points) == 4

    assert all(isinstance(p, Point) for p in points)

    assert points[0].x == 0.0 and points[0].y == 0.0 and points[0].z == 0.0
    assert points[1].x == 1.0 and points[1].y == 0.0 and points[1].z == 0.0

    assert all(p.units == Units.m.value for p in points)


def test_polyline_length(sample_polyline):

    assert pytest.approx(sample_polyline.length) == 4.0

    sample_polyline.closed = False
    assert pytest.approx(sample_polyline.length) == 3.0


def test_polyline_transformation(sample_polyline):
    transform = Transform(matrix=[
        2.0, 0.0, 0.0, 1.0,
        0.0, 2.0, 0.0, 1.0,
        0.0, 0.0, 2.0, 1.0,
        0.0, 0.0, 0.0, 1.0
    ], units=Units.m)

    success, transformed = sample_polyline.transform_to(transform)
    assert success is True

    points = transformed.get_points()

    assert points[0].x == 1.0
    assert points[0].y == 1.0
    assert points[0].z == 1.0

    assert points[1].x == 3.0
    assert points[1].y == 1.0
    assert points[1].z == 1.0

    assert transformed.units == sample_polyline.units


def test_polyline_serialization(sample_polyline):
    serialized = serialize(sample_polyline)
    deserialized = deserialize(serialized)

    assert deserialized.value == sample_polyline.value
    assert deserialized.closed == sample_polyline.closed
    assert deserialized.units == sample_polyline.units
    assert deserialized.domain.start == sample_polyline.domain.start
    assert deserialized.domain.end == sample_polyline.domain.end


def test_polyline_to_list(sample_polyline):
    result = sample_polyline.to_list()

    assert isinstance(result, list)
    assert result[2] == 1
    assert result[3] == 0.0
    assert result[4] == 1.0
    assert result[5] == len(sample_polyline.value)


def test_polyline_from_list():
    input_list = [
        18, "Objects.Geometry.Polyline",
        1,
        0.0, 1.0,
        12,
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0
    ]

    polyline = Polyline.from_list(input_list, Units.m)

    assert polyline.closed is True
    assert len(polyline.value) == 12
    assert polyline.units == Units.m.value
    assert polyline.domain.start == 0.0
    assert polyline.domain.end == 1.0
