# pylint: disable=redefined-outer-name
import pytest

from specklepy.core.api.models.proxies import (
    ColorProxy,
    GroupProxy,
)


@pytest.fixture()
def color_proxy():
    return ColorProxy(
        objects=["app_id_1", "app_id_2"], value=11111, name="color_proxy_name"
    )


@pytest.fixture()
def group_proxy():
    return GroupProxy(objects=["app_id_1", "app_id_2"], name="group_proxy_name")


def create_color_proxy():
    try:
        result = ColorProxy()  # missing parameters
    except AssertionError:
        assert True
    try:
        result = ColorProxy(objects="", value=2, name="")  # wrong type
    except AssertionError:
        assert True

    assert False


def create_group_proxy():
    try:
        result = GroupProxy()  # missing parameters
    except AssertionError:
        assert True
    try:
        result = GroupProxy(objects="", name="")  # wrong type
    except AssertionError:
        assert True
    assert False
