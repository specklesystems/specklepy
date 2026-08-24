from typing import Any, Tuple

from gql import Client, gql

from specklepy.core.api.credentials import Account
from specklepy.core.api.inputs.project_inputs import (
    ProjectInviteCreateInput,
    ProjectInviteUseInput,
)
from specklepy.core.api.models import PendingStreamCollaborator, ProjectWithTeam
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "project_invite"


class ProjectInviteResource(ResourceBase):
    """API Access class for project invites"""

    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        server_version: Tuple[Any, ...] | None,
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def create(
        self, project_id: str, input: ProjectInviteCreateInput
    ) -> ProjectWithTeam:
        request = gql(
            """
            mutation ProjectInviteCreate(
              $projectId: ID!,
              $input: ProjectInviteCreateInput!
              ) {
              data:projectMutations {
                data:invites {
                  data:create(projectId: $projectId, input: $input) {
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
                  }
                }
              }
            }
            """
        )

        request.variable_values = {
            "projectId": project_id,
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ProjectWithTeam]]], request
        ).data.data.data

    def use(self, input: ProjectInviteUseInput) -> bool:
        request = gql(
            """
            mutation ProjectInviteUse($input: ProjectInviteUseInput!) {
              data:projectMutations {
                data:invites {
                  data:use(input: $input)
                }
              }
            }
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[bool]]], request
        ).data.data.data

    def get(
        self, project_id: str, token: str | None
    ) -> PendingStreamCollaborator | None:
        """Returns: The invite, or None if no invite exists"""

        request = gql(
            """
            query ProjectInvite($projectId: String!, $token: String) {
              data:projectInvite(projectId: $projectId, token: $token) {
                id
                inviteId
                invitedBy {
                  avatar
                  bio
                  company
                  id
                  name
                  role
                  verified
                }
                projectId
                projectName
                role
                title
                token
                user {
                  avatar
                  bio
                  company
                  id
                  name
                  role
                  verified
                }
              }
            }
            """
        )

        request.variable_values = {
            "projectId": project_id,
            "token": token,
        }

        return self.make_request_and_parse_response(
            DataResponse[PendingStreamCollaborator | None], request
        ).data

    def cancel(
        self,
        project_id: str,
        invite_id: str,
    ) -> ProjectWithTeam:
        request = gql(
            """
            mutation ProjectInviteCancel($projectId: ID!, $inviteId: String!) {
              data:projectMutations {
                data:invites {
                  data:cancel(projectId: $projectId, inviteId: $inviteId) {
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
            }
            """
        )

        request.variable_values = {
            "projectId": project_id,
            "inviteId": invite_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ProjectWithTeam]]], request
        ).data.data.data
