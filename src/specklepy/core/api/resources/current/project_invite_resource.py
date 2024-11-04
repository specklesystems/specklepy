from typing import Any, Optional, Tuple

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
        server_version: Optional[Tuple[Any, ...]],
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
        QUERY = gql(
            """
            mutation ProjectInviteCreate($projectId: ID!, $input: ProjectInviteCreateInput!) {
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

        variables = {
            "projectId": project_id,
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ProjectWithTeam]]], QUERY, variables
        ).data.data.data

    def use(self, input: ProjectInviteUseInput) -> bool:
        QUERY = gql(
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

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[bool]]], QUERY, variables
        ).data.data.data

    def get(
        self, project_id: str, token: Optional[str]
    ) -> Optional[PendingStreamCollaborator]:
        """Returns: The invite, or None if no invite exists"""

        QUERY = gql(
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

        variables = {
            "projectId": project_id,
            "token": token,
        }

        return self.make_request_and_parse_response(
            DataResponse[Optional[PendingStreamCollaborator]], QUERY, variables
        ).data

    def cancel(
        self,
        project_id: str,
        invite_id: str,
    ) -> ProjectWithTeam:
        QUERY = gql(
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

        variables = {
            "projectId": project_id,
            "inviteId": invite_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ProjectWithTeam]]], QUERY, variables
        ).data.data.data
