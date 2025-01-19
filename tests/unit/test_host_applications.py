import pytest

from specklepy.api.host_applications import (
    _app_name_host_app_mapping,
    get_host_app_from_string,
)


def test_get_host_app_from_string_returns_fallback_app():
    not_existing_app_name = "gmail"
    host_app = get_host_app_from_string(not_existing_app_name)
    assert host_app.name == not_existing_app_name
    assert host_app.slug == not_existing_app_name


@pytest.mark.parametrize("app_name", _app_name_host_app_mapping.keys())
def test_get_host_app_from_string_matches_for_predefined_apps(app_name) -> None:
    host_app = get_host_app_from_string(app_name)
    assert app_name in host_app.slug.lower()
