import pytest

from specklepy.api.client import SpeckleClient
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestWorkspaceResourcePermissions:
    def test_get_projects_with_permissions(self, client: SpeckleClient):
        with pytest.raises(GraphQLException):
            client.workspace.get_projects_with_permissions("not a real id")

    def test_get_projects_with_permissions_returns_correct_type(
        self, client: SpeckleClient
    ):
        assert hasattr(client.workspace, "get_projects_with_permissions")

        method = client.workspace.get_projects_with_permissions
        assert callable(method)
