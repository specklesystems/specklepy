import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Point, PointCloud
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_points():
    return [
        Point(x=0.0, y=0.0, z=0.0, units=Units.m),
        Point(x=1.0, y=0.0, z=0.0, units=Units.m),
        Point(x=0.0, y=1.0, z=0.0, units=Units.m),
        Point(x=1.0, y=1.0, z=0.0, units=Units.m),
    ]


@pytest.fixture
def sample_point_cloud(sample_points):
    return PointCloud(points=sample_points, units=Units.m)


def test_point_cloud_creation(sample_points):
    point_cloud = PointCloud(points=sample_points, units=Units.m)

    assert len(point_cloud.points) == 4
    assert isinstance(point_cloud.points, list)
    assert all(isinstance(p, Point) for p in point_cloud.points)
    assert point_cloud.units == Units.m.value


def test_point_cloud_units(sample_points):
    point_cloud = PointCloud(points=sample_points, units=Units.m)
    assert point_cloud.units == Units.m.value

    point_cloud.units = "mm"
    assert point_cloud.units == "mm"


def test_point_cloud_empty_points():
    point_cloud = PointCloud(points=[], units=Units.m)
    assert len(point_cloud.points) == 0
    assert isinstance(point_cloud.points, list)


def test_point_cloud_serialization(sample_point_cloud):
    serialized = serialize(sample_point_cloud)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, PointCloud)
    assert len(deserialized.points) == len(sample_point_cloud.points)

    for orig_point, deserial_point in zip(
        sample_point_cloud.points, deserialized.points, strict=True
    ):
        assert deserial_point.x == orig_point.x
        assert deserial_point.y == orig_point.y
        assert deserial_point.z == orig_point.z
        assert deserial_point.units == orig_point.units

    assert deserialized.units == sample_point_cloud.units
