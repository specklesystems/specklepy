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
