from gql import gql

from specklepy.core.api.models.current import Workspace
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "workspace"


class WorkspaceResource(ResourceBase):
    """API Access class for models"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def get(self, workspace_id: str) -> Workspace:
        QUERY = gql(
            """
            query WorkspaceGet($workspaceId: String!) {
              data:workspace(id: $workspaceId) {
                id
                name
                role
                slug
                logo
                createdAt
                updatedAt
                readOnly
                description
                permissions {
                  canCreateProject {
                    authorized
                    code
                    message
                  }
                }
              }
            }
            """
        )

        variables = {
            "workspaceId": workspace_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Workspace]], QUERY, variables
        ).data.data
