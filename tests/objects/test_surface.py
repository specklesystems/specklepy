from typing import Any, List, Tuple

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.geometry import ControlPoint, Surface
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


@pytest.fixture
def sample_intervals() -> Tuple[Interval, Interval]:
    return (Interval(start=0.0, end=1.0), Interval(start=0.0, end=1.0))


@pytest.fixture
def sample_point_data() -> List[float]:
    return [
        0.0,
        0.0,
        0.0,
        1.0,  # point 1
        1.0,
        0.0,
        0.0,
        1.0,  # point 2
        0.0,
        1.0,
        0.0,
        1.0,  # point 3
        1.0,
        1.0,
        0.0,
        1.0,  # point 4
    ]


@pytest.fixture
def sample_surface(
    sample_intervals: Tuple[Interval, Interval], sample_point_data: List[float]
) -> Surface:
    domain_u, domain_v = sample_intervals
    return Surface(
        degreeU=1,
        degreeV=1,
        rational=True,
        pointData=sample_point_data,
        countU=2,
        countV=2,
        knotsU=[0.0, 0.0, 1.0, 1.0],
        knotsV=[0.0, 0.0, 1.0, 1.0],
        domainU=domain_u,
        domainV=domain_v,
        closedU=False,
        closedV=False,
        units=Units.m,
    )


@pytest.mark.parametrize("units", [Units.m])
def test_surface_creation(
    sample_intervals: Tuple[Interval, Interval],
    sample_point_data: List[float],
    units: Units,
):
    domain_u, domain_v = sample_intervals
    surface = Surface(
        degreeU=1,
        degreeV=1,
        rational=True,
        pointData=sample_point_data,
        countU=2,
        countV=2,
        knotsU=[0.0, 0.0, 1.0, 1.0],
        knotsV=[0.0, 0.0, 1.0, 1.0],
        domainU=domain_u,
        domainV=domain_v,
        closedU=False,
        closedV=False,
        units=units,
    )

    assert surface.degreeU == 1
    assert surface.degreeV == 1
    assert surface.rational
    assert surface.pointData == sample_point_data
    assert surface.countU == 2
    assert surface.countV == 2
    assert surface.knotsU == [0.0, 0.0, 1.0, 1.0]
    assert surface.knotsV == [0.0, 0.0, 1.0, 1.0]
    assert surface.domainU == domain_u
    assert surface.domainV == domain_v
    assert not surface.closedU
    assert not surface.closedV
    assert surface.units == units.value


@pytest.mark.parametrize("test_value", [1.0])
def test_surface_area(sample_surface: Surface, test_value: float):
    sample_surface.area = test_value
    assert sample_surface.area == test_value


def test_surface_get_control_points(sample_surface: Surface):
    control_points = sample_surface.get_control_points()

    assert len(control_points) == 2
    assert len(control_points[0]) == 2
    assert isinstance(control_points[0][0], ControlPoint)
    assert control_points[0][0].x == 0.0
    assert control_points[0][0].y == 0.0
    assert control_points[0][0].z == 0.0
    assert control_points[0][0].weight == 1.0
    assert control_points[0][0].units == Units.m.value


@pytest.mark.parametrize("units", [Units.m])
def test_surface_set_control_points(sample_surface: Surface, units: Units):
    control_points = [
        [
            ControlPoint(x=0.0, y=0.0, z=0.0, weight=1.0, units=units),
            ControlPoint(x=1.0, y=0.0, z=0.0, weight=1.0, units=units),
        ],
        [
            ControlPoint(x=0.0, y=1.0, z=0.0, weight=1.0, units=units),
            ControlPoint(x=1.0, y=1.0, z=0.0, weight=1.0, units=units),
        ],
    ]

    sample_surface.set_control_points(control_points)

    assert sample_surface.countU == 2
    assert sample_surface.countV == 2
    assert len(sample_surface.pointData) == 16
    assert sample_surface.pointData[0:4] == [0.0, 0.0, 0.0, 1.0]


def test_surface_serialization(sample_surface: Surface):
    serialized = serialize(sample_surface)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Surface)
    assert deserialized.degreeU == sample_surface.degreeU
    assert deserialized.degreeV == sample_surface.degreeV
    assert deserialized.rational == sample_surface.rational
    assert deserialized.pointData == sample_surface.pointData
    assert deserialized.countU == sample_surface.countU
    assert deserialized.countV == sample_surface.countV
    assert deserialized.knotsU == sample_surface.knotsU
    assert deserialized.knotsV == sample_surface.knotsV
    assert deserialized.domainU.start == sample_surface.domainU.start
    assert deserialized.domainU.end == sample_surface.domainU.end
    assert deserialized.domainV.start == sample_surface.domainV.start
    assert deserialized.domainV.end == sample_surface.domainV.end
    assert deserialized.closedU == sample_surface.closedU
    assert deserialized.closedV == sample_surface.closedV
    assert deserialized.units == sample_surface.units


@pytest.mark.parametrize(
    "invalid_param,invalid_value",
    [("degreeU", "not a number")],
)
def test_surface_invalid_construction(
    sample_intervals: Tuple[Interval, Interval],
    invalid_param: str,
    invalid_value: Any,
):
    domain_u, domain_v = sample_intervals

    valid_params = {
        "degreeU": 1,
        "degreeV": 1,
        "rational": True,
        "pointData": [0.0, 0.0, 0.0, 1.0],
        "countU": 1,
        "countV": 1,
        "knotsU": [0.0, 1.0],
        "knotsV": [0.0, 1.0],
        "domainU": domain_u,
        "domainV": domain_v,
        "closedU": False,
        "closedV": False,
        "units": Units.m,
    }
    valid_params[invalid_param] = invalid_value

    with pytest.raises(SpeckleException):
        Surface(**valid_params)
