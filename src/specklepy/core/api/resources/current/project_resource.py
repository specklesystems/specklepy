from typing import Optional

from gql import gql

from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectModelsFilter,
    ProjectUpdateInput,
    ProjectUpdateRoleInput,
)
from specklepy.core.api.models import Project, ProjectWithModels, ProjectWithTeam
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "project"


class ProjectResource(ResourceBase):
    """API Access class for projects"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def get(self, project_id: str) -> Project:
        QUERY = gql(
            """
            query Project($projectId: String!) {
              data:project(id: $projectId) {
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
            }
            """
        )

        variables = {
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[Project], QUERY, variables
        ).data

    def get_with_models(
        self,
        project_id: str,
        *,
        models_limit: int = 25,
        models_cursor: Optional[str] = None,
        models_filter: Optional[ProjectModelsFilter] = None,
    ) -> ProjectWithModels:
        QUERY = gql(
            """
            query ProjectGetWithModels($projectId: String!, $modelsLimit: Int!, $modelsCursor: String, $modelsFilter: ProjectModelsFilter) {
              data:project(id: $projectId) {
                id
                name
                description
                visibility
                allowPublicComments
                role
                createdAt
                updatedAt
                sourceApps
                workspaceId
                models(limit: $modelsLimit, cursor: $modelsCursor, filter: $modelsFilter) {
                  items {
                    id
                    name
                    previewUrl
                    updatedAt
                    displayName
                    description
                    createdAt
                    author {
                      avatar
                      bio
                      company
                      id
                      name
                      role
                      verified
                    }
                  }
                  cursor
                  totalCount
                }
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
            "modelsLimit": models_limit,
            "modelsCursor": models_cursor,
            "modelsFilter": models_filter.model_dump(warnings="error")
            if models_filter
            else None,
        }

        return self.make_request_and_parse_response(
            DataResponse[ProjectWithModels], QUERY, variables
        ).data

    def get_with_team(self, project_id: str) -> ProjectWithTeam:
        QUERY = gql(
            """
            query ProjectGetWithTeam($projectId: String!) {
              data:project(id: $projectId) {
                id
                name
                description
                visibility
                allowPublicComments
                role
                createdAt
                updatedAt
                workspaceId
                sourceApps
                team {
                  id
                  role
                  user {
                    id
                    name
                    bio
                    company
                    avatar
                    verified
                    role
                  }
                }
                invitedTeam {
                  id
                  inviteId
                  projectId
                  projectName
                  title
                  role
                  token
                  user {
                    id
                    name
                    bio
                    company
                    avatar
                    verified
                    role
                  }
                  invitedBy {
                    id
                    name
                    bio
                    company
                    avatar
                    verified
                    role
                  }
                }
                workspaceId
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[ProjectWithTeam], QUERY, variables
        ).data

    def create(self, input: ProjectCreateInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectCreate($input: ProjectCreateInput) {
              data:projectMutations {
                data:create(input: $input) {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  sourceApps
                  workspaceId
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Project]], QUERY, variables
        ).data.data

    def update(self, input: ProjectUpdateInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectUpdate($input: ProjectUpdateInput!) {
              data:projectMutations{
                data:update(update: $input) {
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
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Project]], QUERY, variables
        ).data.data

    def delete(self, project_id: str) -> bool:
        QUERY = gql(
            """
            mutation ProjectDelete($projectId: String!) {
              data:projectMutations {
                data:delete(id: $projectId)
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], QUERY, variables
        ).data.data

    def update_role(self, input: ProjectUpdateRoleInput) -> ProjectWithTeam:
        QUERY = gql(
            """
            mutation ProjectUpdateRole($input: ProjectUpdateRoleInput!) {
              data:projectMutations {
                data:updateRole(input: $input) {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  sourceApps
                  workspaceId
                  team {
                    id
                    role
                    user {
                      id
                      name
                      bio
                      company
                      avatar
                      verified
                      role
                    }
                  }
                  invitedTeam {
                    id
                    inviteId
                    projectId
                    projectName
                    title
                    role
                    token
                    user {
                      id
                      name
                      bio
                      company
                      avatar
                      verified
                      role
                    }
                    invitedBy {
                      id
                      name
                      bio
                      company
                      avatar
                      verified
                      role
                    }
                  }
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ProjectWithTeam]], QUERY, variables
        ).data.data
