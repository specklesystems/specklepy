import pytest
from specklepy.objects.geometry.arc import Arc
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.other import Transform
from specklepy.objects.primitive import Interval
from specklepy.core.api.operations import serialize, deserialize


@pytest.fixture
def sample_arc():
    plane = Plane(
        origin=Point(x=0, y=0, z=0, units="m"),
        normal=Vector(x=0, y=0, z=1, units="m"),
        xdir=Vector(x=1, y=0, z=0, units="m"),
        ydir=Vector(x=0, y=1, z=0, units="m"),
        units="m"
    )

    return Arc(
        plane=plane,
        startPoint=Point(x=1, y=0, z=0, units="m"),
        midPoint=Point(x=0.7071, y=0.7071, z=0, units="m"),
        endPoint=Point(x=0, y=1, z=0, units="m"),
        domain=Interval.unit_interval(),
        units="m"
    )


def test_arc_basic_properties(sample_arc):
    assert pytest.approx(sample_arc.radius, 0.001) == 1.0
    assert sample_arc.units == "m"


def test_arc_transform(sample_arc):
    transform = Transform(matrix=[
        2, 0, 0, 1,
        0, 2, 0, 1,
        0, 0, 2, 1,
        0, 0, 0, 1
    ], units="m")

    success, transformed = sample_arc.transform_to(transform)
    assert success is True
    assert pytest.approx(transformed.radius, 0.001) == 2.0


def test_arc_serialization(sample_arc):
    serialized = serialize(sample_arc)
    deserialized = deserialize(serialized)

    assert deserialized.units == sample_arc.units
    assert pytest.approx(deserialized.radius, 0.001) == sample_arc.radius

    assert pytest.approx(deserialized.startPoint.x,
                         0.001) == sample_arc.startPoint.x
    assert pytest.approx(deserialized.startPoint.y,
                         0.001) == sample_arc.startPoint.y
    assert pytest.approx(deserialized.startPoint.z,
                         0.001) == sample_arc.startPoint.z

    assert pytest.approx(deserialized.midPoint.x,
                         0.001) == sample_arc.midPoint.x
    assert pytest.approx(deserialized.midPoint.y,
                         0.001) == sample_arc.midPoint.y
    assert pytest.approx(deserialized.midPoint.z,
                         0.001) == sample_arc.midPoint.z

    assert pytest.approx(deserialized.endPoint.x,
                         0.001) == sample_arc.endPoint.x
    assert pytest.approx(deserialized.endPoint.y,
                         0.001) == sample_arc.endPoint.y
    assert pytest.approx(deserialized.endPoint.z,
                         0.001) == sample_arc.endPoint.z


def test_arc_measure(sample_arc):
    assert pytest.approx(sample_arc.measure, 0.001) == 1.5708


def test_arc_length(sample_arc):
    assert pytest.approx(sample_arc.length, 0.001) == 1.5708


def test_arc_domain(sample_arc):
    assert sample_arc.domain.start == 0.0
    assert sample_arc.domain.end == 1.0
    assert sample_arc._domain == sample_arc.domain


def test_arc_to_list():
    plane = Plane(
        origin=Point(x=0.0, y=0.0, z=0.0, units="m"),
        normal=Vector(x=0.0, y=0.0, z=1.0, units="m"),
        xdir=Vector(x=1.0, y=0.0, z=0.0, units="m"),
        ydir=Vector(x=0.0, y=1.0, z=0.0, units="m"),
        units="m"
    )
    arc = Arc(
        plane=plane,
        startPoint=Point(x=1.0, y=0.0, z=0.0, units="m"),
        midPoint=Point(x=0.7071, y=0.7071, z=0.0, units="m"),
        endPoint=Point(x=0.0, y=1.0, z=0.0, units="m"),
        domain=Interval(start=0.0, end=1.0),
        units="m"
    )

    coords = arc.to_list()
    assert len(coords) == 28  # total_length, type, units_encoding + data
    assert coords[0] == 28  # total length
    assert coords[1] == "Objects.Geometry.Arc"  # speckle type
    assert coords[5:7] == [0.0, 1.0]  # domain
    # Check plane coordinates
    assert coords[7:10] == [0.0, 0.0, 0.0]  # plane origin
    assert coords[10:13] == [0.0, 0.0, 1.0]  # plane normal
    assert coords[13:16] == [1.0, 0.0, 0.0]  # plane xdir
    assert coords[16:19] == [0.0, 1.0, 0.0]  # plane ydir
    # Check point coordinates
    assert coords[19:22] == [1.0, 0.0, 0.0]  # start point
    assert coords[22:25] == [0.7071, 0.7071, 0.0]  # mid point
    assert coords[25:28] == [0.0, 1.0, 0.0]  # end point


def test_arc_from_list():
    coords = [
        28, "Objects.Geometry.Arc", 3,  # header
        1.0, 1.5708,  # radius, measure
        0.0, 1.0,  # domain
        0.0, 0.0, 0.0,  # plane origin
        0.0, 0.0, 1.0,  # plane normal
        1.0, 0.0, 0.0,  # plane xdir
        0.0, 1.0, 0.0,  # plane ydir
        1.0, 0.0, 0.0,  # start point
        0.7071, 0.7071, 0.0,  # mid point
        0.0, 1.0, 0.0   # end point
    ]

    arc = Arc.from_list(coords)
    assert arc.units == "m"
    assert arc.domain.start == 0.0
    assert arc.domain.end == 1.0
    assert arc.startPoint.x == 1.0
    assert arc.startPoint.y == 0.0
    assert arc.startPoint.z == 0.0
    assert abs(arc.midPoint.x - 0.7071) < 0.0001
    assert abs(arc.midPoint.y - 0.7071) < 0.0001
    assert arc.midPoint.z == 0.0
    assert arc.endPoint.x == 0.0
    assert arc.endPoint.y == 1.0
    assert arc.endPoint.z == 0.0
