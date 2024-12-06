# pylint: disable=redefined-outer-name
import pytest

from specklepy.core.api.models.proxies import ColorProxy, GroupProxy
from specklepy.objects.other import RenderMaterial, RenderMaterialProxy


@pytest.fixture()
def color_proxy():
    return ColorProxy(
        objects=["app_id_1", "app_id_2"], value=11111, name="color_proxy_name"
    )


@pytest.fixture()
def group_proxy():
    return GroupProxy(objects=["app_id_1", "app_id_2"], name="group_proxy_name")


@pytest.fixture()
def material():
    return RenderMaterial(
        name="name", opacity=0.3, metalness=0, roughness=0, diffuse=1, emissive=1
    )


@pytest.fixture()
def material_proxy():
    return RenderMaterialProxy(objects=["app_id_1", "app_id_2"], value=material())


def test_create_color_proxy():
    try:
        ColorProxy(objects="", value=2, name="")  # wrong type
        assert False
    except TypeError:
        assert True
    except:
        assert False


def test_create_group_proxy():
    try:
        GroupProxy(objects="", name="")  # wrong type
        assert False
    except TypeError:
        assert True
    except:
        assert False


def test_create_material_proxy():
    try:
        RenderMaterialProxy(objects="", name="")  # wrong type
        assert False
    except TypeError:
        assert True
    except:
        assert False
