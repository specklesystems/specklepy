import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Curve, Plane, Point, Polyline, Vector
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_polyline():
    """
    sample polyline
    """
    return Polyline(value=[0, 0, 0, 1, 0, 0, 1, 1, 0], units=Units.m)


@pytest.fixture
def sample_plane():
    """
    sample plane for bbox creation
    """
    origin = Point(x=0, y=0, z=0, units=Units.m)
    normal = Vector(x=0, y=0, z=1, units=Units.m)
    xdir = Vector(x=1, y=0, z=0, units=Units.m)
    ydir = Vector(x=0, y=1, z=0, units=Units.m)
    return Plane(origin=origin, normal=normal, xdir=xdir, ydir=ydir, units=Units.m)


@pytest.fixture
def sample_curve(sample_polyline):
    """
    sample curve for testing
    """
    return Curve(
        degree=3,
        periodic=False,
        rational=False,
        points=[0, 0, 0, 1, 1, 0, 2, 0, 0, 3, 1, 0],
        weights=[1, 1, 1, 1],
        knots=[0, 0, 0, 0, 1, 1, 1, 1],
        closed=False,
        displayValue=sample_polyline,
        units=Units.m,
    )


def test_curve_creation(sample_polyline):
    """
    test curve initialization
    """
    curve = Curve(
        degree=3,
        periodic=False,
        rational=False,
        points=[0, 0, 0, 1, 1, 0, 2, 0, 0, 3, 1, 0],
        weights=[1, 1, 1, 1],
        knots=[0, 0, 0, 0, 1, 1, 1, 1],
        closed=False,
        displayValue=sample_polyline,
        units=Units.m,
    )

    assert curve.degree == 3
    assert curve.periodic is False
    assert curve.rational is False
    assert curve.points == [0, 0, 0, 1, 1, 0, 2, 0, 0, 3, 1, 0]
    assert curve.weights == [1, 1, 1, 1]
    assert curve.knots == [0, 0, 0, 0, 1, 1, 1, 1]
    assert curve.closed is False
    assert curve.units == Units.m.value
    assert curve.displayValue == sample_polyline


def test_length_property(sample_polyline):
    """
    test the length property setter and getter
    """
    curve = Curve(
        degree=1,
        periodic=False,
        rational=False,
        points=[0, 0, 0, 1, 0, 0],
        weights=[1, 1],
        knots=[0, 0, 1, 1],
        closed=False,
        displayValue=sample_polyline,
        units=Units.m,
    )

    assert curve.length == 0.0

    curve.length = 1.5
    assert curve.length == 1.5


def test_area_property(sample_polyline):
    """
    test the area property setter and getter
    """
    polyline = Polyline(
        value=[0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0], units=Units.m
    )

    curve = Curve(
        degree=1,
        periodic=False,
        rational=False,
        points=[0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0],
        weights=[1, 1, 1, 1, 1],
        knots=[0, 0, 1, 2, 3, 4, 4],
        closed=True,
        displayValue=polyline,
        units=Units.m,
    )

    assert curve.area == 0.0

    curve.area = 1.0
    assert curve.area == 1.0


def test_curve_serialization(sample_curve):
    """
    test serialization and deserialization of the curve
    """
    serialized = serialize(sample_curve)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Curve)
    assert deserialized.degree == sample_curve.degree
    assert deserialized.periodic == sample_curve.periodic
    assert deserialized.rational == sample_curve.rational
    assert deserialized.points == sample_curve.points
    assert deserialized.weights == sample_curve.weights
    assert deserialized.knots == sample_curve.knots
    assert deserialized.closed == sample_curve.closed
    assert deserialized.units == sample_curve.units


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_curve_units(sample_polyline, new_units):
    """
    test changing units of a curve
    """
    curve = Curve(
        degree=3,
        periodic=False,
        rational=False,
        points=[0, 0, 0, 1, 1, 0, 2, 0, 0, 3, 1, 0],
        weights=[1, 1, 1, 1],
        knots=[0, 0, 0, 0, 1, 1, 1, 1],
        closed=False,
        displayValue=sample_polyline,
        units=Units.m,
    )

    assert curve.units == Units.m.value

    curve.units = new_units
    assert curve.units == new_units
