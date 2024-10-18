from typing import Optional

from gql import gql

from specklepy.core.api.inputs.project_inputs import (
    ProjectInviteCreateInput,
)
from specklepy.core.api.models import Project, ProjectMutation
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "project"


class ProjectInviteResource(ResourceBase):
    """API Access class for project invites"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def create(self, project_id: str, input: ProjectInviteCreateInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectInviteCreate($projectId: ID!, $input: ProjectInviteCreateInput!) {
              projectMutations {
                invites {
                  create(projectId: $projectId, input: $input) {
                    id
                    name
                    description
                    visibility
                    allowPublicComments
                    role
                    createdAt
                    updatedAt
                    team {
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
            }
            """
        )

        params = {"projectId": project_id, "input": input}

        return self.make_request_and_parse_response(
            DataResponse[ProjectMutation], QUERY, params
        ).data.invites.create

    def get_with_models(
        self,
        project_id: str,
        models_limit: int = 25,
        models_cursor: Optional[str] = None,
        models_filter: Optional[ProjectModelsFilter] = None,
    ) -> Project:
        QUERY = gql(
            """
            query ProjectGetWithModels($projectId: String!, $modelsLimit: Int!, $modelsCursor: String, $modelsFilter: ProjectModelsFilter) {
              project(id: $projectId) {
                id
                name
                description
                visibility
                allowPublicComments
                role
                createdAt
                updatedAt
                sourceApps
                models(limit: $modelsLimit, cursor: $modelsCursor, filter: $modelsFilter) {
                  items {
                    id
                    name
                    previewUrl
                    updatedAt
                    displayName
                    description
                    createdAt
                  }
                  cursor
                  totalCount
                }
              }
            }
            """
        )

        params = {
            "projectId": project_id,
            "modelsLimit": models_limit,
            "modelsCursor": models_cursor,
            "modelsFilter": models_filter,
        }

        return self.make_request(query=QUERY, params=params, return_type="project")

    def get_with_team(self, project_id: str) -> Project:
        QUERY = gql(
            """
            query ProjectGetWithTeam($projectId: String!) {
              project(id: $projectId) {
                id
                name
                description
                visibility
                allowPublicComments
                role
                createdAt
                updatedAt
                team {
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

        params = {"projectId": project_id}

        return self.make_request(query=QUERY, params=params, return_type="project")

    def create(self, input: ProjectCreateInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectCreate($input: ProjectCreateInput) {
              projectMutations {
                create(input: $input) {
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

        params = {"input": input}

        return self.make_request(
            query=QUERY, params=params, return_type="projectMutations"
        ).create

    def update(self, input: ProjectUpdateInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectUpdate($input: ProjectUpdateInput!) {
              projectMutations{
                update(update: $input) {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  workspaceId
                }
              }
            }
            """
        )

        params = {"input": input}

        return self.make_request(
            query=QUERY, params=params, return_type="projectMutations"
        ).update

    def delete(self, project_id: str) -> Project:
        QUERY = gql(
            """
            mutation ProjectDelete($projectId: String!) {
              projectMutations {
                delete(id: $projectId)
              }
            }
            """
        )

        params = {"projectId": project_id}

        return self.make_request(
            query=QUERY, params=params, return_type="projectMutations"
        ).delete

    def update_role(self, input: ProjectUpdateRoleInput) -> Project:
        QUERY = gql(
            """
            mutation ProjectUpdateRole($input: ProjectUpdateRoleInput!) {
              projectMutations {
                updateRole(input: $input) {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  team {
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
            }
            """
        )

        params = {"input": input}

        return self.make_request(
            query=QUERY,
            params=params,
            return_type=["projectMutations", "delete"],
            schema=ProjectMutation,
        )
