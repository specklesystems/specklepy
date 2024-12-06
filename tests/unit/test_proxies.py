# pylint: disable=redefined-outer-name
import pytest

from specklepy.core.api.models.proxies import ColorProxy, GroupProxy


@pytest.fixture()
def color_proxy():
    return ColorProxy(
        objects=["app_id_1", "app_id_2"], value=11111, name="color_proxy_name"
    )


@pytest.fixture()
def group_proxy():
    return GroupProxy(objects=["app_id_1", "app_id_2"], name="group_proxy_name")


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
