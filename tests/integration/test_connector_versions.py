import pytest
from httpx import HTTPStatusError

from specklepy.core.api.connector_versions import (
    ConnectorVersion,
    ConnectorVersions,
    get_connector_versions,
    get_latest_version,
)

# NOTE: the tests in this file are testing against the live releases.speckle.dev server
# url defined in get_connector_versions.


def test_connector_versions():
    res = get_connector_versions("blender")

    assert isinstance(res, ConnectorVersions)
    assert res.versions  # Assuming the feed is not empty


def test_get_latest_version_throws_no_slug():
    with pytest.raises(HTTPStatusError) as ex:
        get_latest_version("non-existent-connector!", True)

    assert "404" in str(ex.value)


def test_get_latest_version():
    res = get_latest_version("blender", False)

    assert isinstance(res, ConnectorVersion)
