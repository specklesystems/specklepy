from typing import Optional

from gql import gql

from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectModelsFilter,
    ProjectUpdateInput,
    ProjectUpdateRoleInput,
    WorkspaceProjectCreateInput,
)
from specklepy.core.api.inputs.user_inputs import UserProjectsFilter
from specklepy.core.api.models import (
    Project,
    ProjectWithModels,
    ProjectWithTeam,
    ResourceCollection,
)
from specklepy.core.api.models.current import (
    ProjectPermissionChecks,
    ProjectWithPermissions,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import GraphQLException

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

    def get_permissions(self, project_id: str) -> ProjectPermissionChecks:
        QUERY = gql(
            """
            query Project($projectId: String!) {
              data:project(id: $projectId) {
                data:permissions {
                  canCreateModel {
                    authorized
                    code
                    message
                  }
                  canDelete {
                    authorized
                    code
                    message
                  }
                  canLoad {
                    authorized
                    code
                    message
                  }
                  canPublish {
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
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ProjectPermissionChecks]], QUERY, variables
        ).data.data

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
            query ProjectGetWithModels(
              $projectId: String!,
              $modelsLimit: Int!,
              $modelsCursor: String,
              $modelsFilter: ProjectModelsFilter
              ) {
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
                models(
                  limit: $modelsLimit,
                  cursor: $modelsCursor,
                  filter: $modelsFilter
                  ) {
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
            "modelsFilter": (
                models_filter.model_dump(warnings="error", by_alias=True)
                if models_filter
                else None
            ),
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
        """
        Creates a non-workspace project (aka Personal Project)

        see client.active_user.can_create_personal_projects to see if the user has
        permission
        """
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
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Project]], QUERY, variables
        ).data.data

    def create_in_workspace(self, input: WorkspaceProjectCreateInput) -> Project:
        """
        Creates a workspace project
        This feature is only supported by Workspace Enabled Servers
        (e.g. app.speckle.systems)

        see `workspace.permissions.can_create_project` to see if the user has permission
        """
        QUERY = gql(
            """
          mutation WorkspaceProjectCreate($input: WorkspaceProjectCreateInput!) {
            data:workspaceMutations {
              data:projects {
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
          }
          """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[Project]]], QUERY, variables
        ).data.data.data

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
            "input": input.model_dump(warnings="error", by_alias=True),
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
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ProjectWithTeam]], QUERY, variables
        ).data.data

    def get_projects_with_permissions(
        self,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[UserProjectsFilter] = None,
    ) -> ResourceCollection[ProjectWithPermissions]:
        """
        Gets the currently active user's projects with their permissions.
        This is useful for checking what actions can be performed on each project.
        """
        QUERY = gql(
            """
             query User($limit : Int!, $cursor: String, $filter: UserProjectsFilter) {
              data:activeUser {
                data:projects(limit: $limit, cursor: $cursor, filter: $filter) {
                   totalCount
                   cursor
                   items {
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
                      permissions {
                        canCreateModel {
                          code
                          authorized
                          message
                        }
                        canDelete {
                          code
                          authorized
                          message
                        }
                        canLoad {
                          code
                          authorized
                          message
                        }
                        canPublish {
                          code
                          authorized
                          message
                        }
                      }
                   }
                }
              }
            }
            """
        )

        variables = {
            "limit": limit,
            "cursor": cursor,
            "filter": filter.model_dump(warnings="error", by_alias=True)
            if filter
            else None,
        }

        response = self.make_request_and_parse_response(
            DataResponse[
                Optional[DataResponse[ResourceCollection[ProjectWithPermissions]]]
            ],
            QUERY,
            variables,
        )

        if response.data is None:
            raise GraphQLException(
                "GraphQL response indicated that the ActiveUser could not be found"
            )

        return response.data.data
