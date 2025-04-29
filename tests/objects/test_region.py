# ignoring "line too long" check from linter
# to match with SpeckleExceptions
# ruff: noqa: E501

import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry.polyline import Polyline
from specklepy.objects.geometry.region import Region
from specklepy.objects.models.units import Units


@pytest.fixture
def sample_boundary():
    return Polyline(
        # possibly replace same start-end Polyline point with "closed" property
        value=[-10, -10, 0, 10, -10, 0, 10, 10, 0, -10, 10, 0, -10, -10, 0],
        units=Units.m,
    )


@pytest.fixture
def sample_loop1():
    return Polyline(
        # possibly replace same start-end Polyline point with "closed" property
        value=[-9, -9, 0, -5, -9, 0, -5, -5, 0, -9, -5, 0, -9, -9, 0],
        units=Units.m,
    )


@pytest.fixture
def sample_loop2():
    return Polyline(
        # possibly replace same start-end Polyline point with "closed" property
        value=[5, 5, 0, 9, 5, 0, 9, 9, 0, 5, 9, 0, 5, 5, 0],
        units=Units.m,
    )


@pytest.fixture
def sample_region(sample_boundary, sample_loop1, sample_loop2):
    return Region(
        boundary=sample_boundary,
        innerLoops=[sample_loop1, sample_loop2],
        hasHatchPattern=True,
        units=Units.m,
        displayValue=[],
    )


def test_region_creation(sample_boundary, sample_loop1, sample_loop2):
    has_hatch_pattern = True
    region = Region(
        boundary=sample_boundary,
        innerLoops=[sample_loop1, sample_loop2],
        hasHatchPattern=has_hatch_pattern,
        units=Units.m,
        displayValue=[],
    )
    assert region.boundary == sample_boundary
    assert region.innerLoops[0] == sample_loop1
    assert region.innerLoops[1] == sample_loop2
    assert region.hasHatchPattern == has_hatch_pattern
    assert len(region.displayValue) == 0
    assert region.units == Units.m.value


def test_region_serialization(sample_region):
    serialized = serialize(sample_region)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, Region)
    assert deserialized.hasHatchPattern == sample_region.hasHatchPattern
    assert deserialized.units == sample_region.units

    assert deserialized.boundary.length == sample_region.boundary.length
    assert deserialized.boundary.domain.length == sample_region.boundary.domain.length
    assert deserialized.boundary.domain.start == sample_region.boundary.domain.start
    assert deserialized.boundary.domain.end == sample_region.boundary.domain.end

    for i, loop in enumerate(sample_region.innerLoops):
        assert deserialized.innerLoops[i].length == loop.length
        assert deserialized.innerLoops[i].domain.length == loop.domain.length
        assert deserialized.innerLoops[i].domain.start == loop.domain.start
        assert deserialized.innerLoops[i].domain.end == loop.domain.end
