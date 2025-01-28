import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import ControlPoint
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_control_point():
    return ControlPoint(
        x=1.0,
        y=2.0,
        z=3.0,
        weight=1.0,
        units=Units.m
    )


def test_control_point_creation():
    control_point = ControlPoint(
        x=1.0,
        y=2.0,
        z=3.0,
        weight=1.0,
        units=Units.m
    )

    assert control_point.x == 1.0
    assert control_point.y == 2.0
    assert control_point.z == 3.0
    assert control_point.weight == 1.0
    assert control_point.units == Units.m.value


def test_control_point_units():
    control_point = ControlPoint(
        x=1.0,
        y=2.0,
        z=3.0,
        weight=1.0,
        units=Units.m
    )

    assert control_point.units == Units.m.value

    # Test setting units with string
    control_point.units = "mm"
    assert control_point.units == "mm"


def test_control_point_invalid_construction():
    with pytest.raises(Exception):
        ControlPoint(
            x="not a number",
            y=2.0,
            z=3.0,
            weight=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        ControlPoint(
            x=1.0,
            y="not a number",
            z=3.0,
            weight=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        ControlPoint(
            x=1.0,
            y=2.0,
            z="not a number",
            weight=1.0,
            units=Units.m
        )

    with pytest.raises(Exception):
        ControlPoint(
            x=1.0,
            y=2.0,
            z=3.0,
            weight="not a number",
            units=Units.m
        )


def test_control_point_serialization(sample_control_point):
    serialized = serialize(sample_control_point)
    deserialized = deserialize(serialized)

    assert deserialized.x == sample_control_point.x
    assert deserialized.y == sample_control_point.y
    assert deserialized.z == sample_control_point.z
    assert deserialized.weight == sample_control_point.weight
    assert deserialized.units == sample_control_point.units
