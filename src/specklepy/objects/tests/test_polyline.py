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


def test_polyline_to_list():
    polyline = Polyline(
        value=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        closed=True,
        domain=Interval(start=0.0, end=1.0),
        units="m"
    )
    coords = polyline.to_list()
    assert coords[3] == 1  # is_closed (True = 1)
    assert coords[4:6] == [0.0, 1.0]  # domain
    assert coords[6] == 6  # coords_count
    assert coords[7:] == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]  # coordinates


def test_polyline_from_list():
    coords = [11, "Objects.Geometry.Polyline", 3,  # header
              1,  # closed
              0.0, 1.0,  # domain
              6,  # coords_count
              1.0, 2.0, 3.0, 4.0, 5.0, 6.0]  # coordinates
    polyline = Polyline.from_list(coords, "m")
    assert polyline.closed is True
    assert polyline.domain.start == 0.0
    assert polyline.domain.end == 1.0
    assert polyline.value == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    assert polyline.units == "m"
