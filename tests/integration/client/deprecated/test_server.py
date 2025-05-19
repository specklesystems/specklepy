import pytest

from specklepy.api.client import SpeckleClient
from specklepy.api.models import ServerInfo


@pytest.fixture(scope="module")
def token_info():
    return {
        "token": None,
        "name": "super secret token",
        "scopes": ["streams:read", "streams:write"],
        "lifespan": 9001,
    }


@pytest.skip(
    "Docker yml file is not configured to return the canonical url properly enough for server.get to fetch the fe2 headers"
)
def test_server_get(client: SpeckleClient):
    server = client.server.get()

    assert isinstance(server, ServerInfo)
    assert isinstance(server.frontend2, bool)


def test_server_version(client: SpeckleClient):
    version = client.server.version()

    assert isinstance(version, tuple)
    if len(version) == 1:
        assert version[0] == "dev"
    else:
        assert isinstance(version[0], int)
        assert len(version) >= 3


def test_server_apps(client: SpeckleClient):
    apps = client.server.apps()

    assert isinstance(apps, list)
    assert len(apps) >= 1
    assert any(app["name"] == "Speckle Web Manager" for app in apps)


def test_server_create_token(client, token_info):
    token_info["token"] = client.server.create_token(
        name=token_info["name"],
        scopes=token_info["scopes"],
        lifespan=token_info["lifespan"],
    )

    assert isinstance(token_info["token"], str)


def test_server_revoke_token(client, token_info):
    revoked = client.server.revoke_token(token=token_info["token"])

    assert revoked is True
