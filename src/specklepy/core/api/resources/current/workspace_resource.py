from typing import Optional

from gql import gql

from specklepy.core.api.inputs.project_inputs import WorksaceProjectsFilter
from specklepy.core.api.models.current import Project, ResourceCollection, Workspace
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
                creationState
                {
                  completed
                }
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
            DataResponse[Workspace], QUERY, variables
        ).data

    def get_projects(
        self,
        workspace_id: str,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[WorksaceProjectsFilter] = None,
    ) -> ResourceCollection[Project]:
        QUERY = gql(
            """
            query Workspace($workspaceId: String!, $limit: Int!, $cursor: String, $filter: WorkspaceProjectsFilter) {
              data:workspace(id: $workspaceId) {
                data:projects(limit: $limit, cursor: $cursor, filter: $filter) {
                  cursor
                  items {
                    allowPublicComments
                    createdAt
                    description
                    id
                    name
                    role
                    sourceApps
                    updatedAt
                    visibility
                    workspaceId
                  }
                  totalCount
                }
              }
            }
            """  # noqa: E501
        )

        variables = {
            "workspaceId": workspace_id,
            "limit": limit,
            "cursor": cursor,
            "filter": filter.model_dump(warnings="error", by_alias=True)
            if filter
            else None,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ResourceCollection[Project]]], QUERY, variables
        ).data.data
