# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import ControlPoint
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_control_point():
    return ControlPoint(x=1.0, y=2.0, z=3.0, weight=1.0, units=Units.m)


@pytest.mark.parametrize(
    "x,y,z,weight,expected_units", [(1.0, 2.0, 3.0, 1.0, Units.m.value)]
)
def test_control_point_creation(x, y, z, weight, expected_units):
    control_point = ControlPoint(x=x, y=y, z=z, weight=weight, units=Units.m)
    assert control_point.x == x
    assert control_point.y == y
    assert control_point.z == z
    assert control_point.weight == weight
    assert control_point.units == expected_units


@pytest.mark.parametrize("new_units", ["mm", "cm", "in"])
def test_control_point_units(new_units):
    control_point = ControlPoint(x=1.0, y=2.0, z=3.0, weight=1.0, units=Units.m)
    assert control_point.units == Units.m.value
    control_point.units = new_units
    assert control_point.units == new_units


@pytest.mark.parametrize(
    "invalid_param, test_params, error_msg",
    [
        (
            "x",
            {"x": "not a number", "y": 2.0, "z": 3.0, "weight": 1.0},
            "Cannot set 'ControlPoint.x':it expects type '<class 'float'>',but received type 'str'",
        ),
        (
            "y",
            {"x": 1.0, "y": "not a number", "z": 3.0, "weight": 1.0},
            "Cannot set 'ControlPoint.y':it expects type '<class 'float'>',but received type 'str'",
        ),
        (
            "z",
            {"x": 1.0, "y": 2.0, "z": "not a number", "weight": 1.0},
            "Cannot set 'ControlPoint.z':it expects type '<class 'float'>',but received type 'str'",
        ),
        (
            "weight",
            {"x": 1.0, "y": 2.0, "z": 3.0, "weight": "not a number"},
            "Cannot set 'ControlPoint.weight':it expects type '<class 'float'>',but received type 'str'",
        ),
    ],
)
def test_control_point_invalid_construction(invalid_param, test_params, error_msg):
    with pytest.raises(SpeckleException) as exc_info:
        ControlPoint(**test_params, units=Units.m)
    assert str(exc_info.value) == f"SpeckleException: {error_msg}"


def test_control_point_serialization(sample_control_point):
    serialized = serialize(sample_control_point)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, ControlPoint)
    assert deserialized.x == sample_control_point.x
    assert deserialized.y == sample_control_point.y
    assert deserialized.z == sample_control_point.z
    assert deserialized.weight == sample_control_point.weight
    assert deserialized.units == sample_control_point.units
