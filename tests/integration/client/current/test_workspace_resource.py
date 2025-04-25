import pytest

from specklepy.api.client import SpeckleClient
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestWorkspaceResource:
    def test_get_workspace(self, client: SpeckleClient):
        """
        Test server is not workspace enabled, so we can't really test everything here
        We'll just test client's error handling
        """
        with pytest.raises(GraphQLException):
            client.workspace.get("not a real id")
