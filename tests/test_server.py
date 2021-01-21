import pytest
from speckle.api.models import ServerInfo


class TestServer:
    def test_server_get(self, client):
        server = client.server.get()

        assert isinstance(server, ServerInfo)

    def test_apps(self, client):
        apps = client.server.apps()

        assert isinstance(apps, list)
        assert len(apps) >= 1
        assert any(app["name"] == "Speckle Web Manager" for app in apps)
