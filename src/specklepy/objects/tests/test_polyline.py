import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Point, Polyline
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def open_square_coords():
    return [
        0.0,
        0.0,
        0.0,  # point 1
        1.0,
        0.0,
        0.0,  # point 2
        1.0,
        1.0,
        0.0,  # point 3
        0.0,
        1.0,
        0.0,  # point 4
    ]


@pytest.fixture
def closed_square_coords():
    return [
        0.0,
        0.0,
        0.0,  # point 1
        1.0,
        0.0,
        0.0,  # point 2
        1.0,
        1.0,
        0.0,  # point 3
        0.0,
        1.0,
        0.0,  # point 4
        0.0,
        0.0,
        0.0,  # point 5 (same as point 1)
    ]


@pytest.fixture
def sample_polyline(open_square_coords):
    return Polyline(value=open_square_coords, units=Units.m)


def test_polyline_creation(open_square_coords):
    polyline = Polyline(value=open_square_coords, units=Units.m)
    assert polyline.value == open_square_coords
    assert polyline.units == Units.m.value
    assert polyline.closed is False


def test_polyline_domain(sample_polyline):
    assert isinstance(sample_polyline.domain, Interval)
    assert sample_polyline.domain.start == 0.0
    assert sample_polyline.domain.end == 1.0


def test_polyline_is_closed(open_square_coords, closed_square_coords):
    # Test the static method
    assert not Polyline.is_closed(open_square_coords)
    assert Polyline.is_closed(closed_square_coords)

    # Test with closed flag
    open_poly = Polyline(value=open_square_coords, units=Units.m)
    closed_poly = Polyline(value=closed_square_coords, units=Units.m, closed=True)
    assert not open_poly.closed
    assert closed_poly.closed


def test_polyline_is_closed_with_tolerance(open_square_coords):
    almost_closed = open_square_coords + [
        0.0,
        0.0,
        0.001,  # last point slightly above start
    ]
    # Test static method with tolerance
    assert not Polyline.is_closed(almost_closed, tolerance=1e-6)
    assert Polyline.is_closed(almost_closed, tolerance=0.01)

    # Also test with instance
    poly = Polyline(value=almost_closed, units=Units.m)
    # poly.closed should reflect what was passed in construction, not computed
    assert not poly.closed


def test_polyline_length_open(sample_polyline):
    sample_polyline.length = sample_polyline.calculate_length()
    assert sample_polyline.length == 3.0


def test_polyline_length_closed(closed_square_coords):
    polyline = Polyline(value=closed_square_coords, units=Units.m, closed=True)
    polyline.length = polyline.calculate_length()
    assert polyline.length == 4.0


def test_polyline_get_points(sample_polyline):
    points = sample_polyline.get_points()
    assert len(points) == 4
    assert all(isinstance(p, Point) for p in points)
    assert all(p.units == Units.m.value for p in points)

    # Create expected points
    expected_points = [
        Point(x=0.0, y=0.0, z=0.0, units=Units.m),
        Point(x=1.0, y=0.0, z=0.0, units=Units.m),
        Point(x=1.0, y=1.0, z=0.0, units=Units.m),
        Point(x=0.0, y=1.0, z=0.0, units=Units.m),
    ]

    # Check coordinates match
    for actual, expected in zip(points, expected_points, strict=False):
        assert actual.x == expected.x
        assert actual.y == expected.y
        assert actual.z == expected.z


def test_polyline_invalid_coordinates():
    invalid_coords = [0.0, 0.0, 0.0, 1.0, 1.0]  # missing one coordinate
    with pytest.raises(ValueError):
        polyline = Polyline(value=invalid_coords, units=Units.m)
        polyline.get_points()


def test_polyline_units(open_square_coords):
    polyline = Polyline(value=open_square_coords, units=Units.m)
    assert polyline.units == Units.m.value
    polyline.units = "mm"
    assert polyline.units == "mm"


def test_polyline_closed_flag(open_square_coords, closed_square_coords):
    # Test default value
    poly1 = Polyline(value=open_square_coords, units=Units.m)
    assert poly1.closed is False

    # Test explicit value
    poly2 = Polyline(value=closed_square_coords, units=Units.m, closed=True)
    assert poly2.closed is True


def test_polyline_serialization(sample_polyline):
    serialized = serialize(sample_polyline)
    deserialized = deserialize(serialized)
    assert deserialized.value == sample_polyline.value
    assert deserialized.units == sample_polyline.units
    assert deserialized.domain.start == sample_polyline.domain.start
    assert deserialized.domain.end == sample_polyline.domain.end
    assert deserialized.closed == sample_polyline.closed
