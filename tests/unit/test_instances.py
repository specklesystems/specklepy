# pylint: disable=redefined-outer-name
import pytest

from specklepy.core.api.models.instances import InstanceDefinitionProxy, InstanceProxy


@pytest.fixture()
def instance_proxy():
    return InstanceProxy(
        definitionId="definitionId", transform=[1, 23.5], units="unit", maxDepth=3
    )


@pytest.fixture()
def instance_definition_proxy():
    return InstanceDefinitionProxy(
        objects=["app_id_1", "app_id_2"], maxDepth=2, name="group_proxy_name"
    )


def test_create_instance_proxy():
    try:
        InstanceProxy(definitionId="", transform="", units="", maxDepth=1)  # wrong type
        assert False
    except TypeError:
        assert True
    except:
        assert False


def test_create_instance_definition_proxy():
    try:
        InstanceDefinitionProxy(objects="", maxDepth=1, name="")  # wrong type
        assert False
    except TypeError:
        assert True
    except:
        assert False
