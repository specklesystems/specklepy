from typing import List, Optional

from gql import gql

from specklepy.core.api.inputs.user_inputs import UserProjectsFilter, UserUpdateInput
from specklepy.core.api.models import (
    PendingStreamCollaborator,
    Project,
    ResourceCollection,
    User,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import GraphQLException

NAME = "active_user"


class ActiveUserResource(ResourceBase):
    """API Access class for the active user"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )
        self.schema = User

    def get(self) -> Optional[User]:
        """Gets the currently active user profile
        (as extracted from the authorization header)

        Returns:
            User -- the requested user, or none if no authentication token
            is provided to the Client
        """
        QUERY = gql(
            """
            query User {
             data:activeUser {
               id
               email
               name
               bio
               company
               avatar
               verified
               role
             }
           }
           """
        )

        variables = {}

        return self.make_request_and_parse_response(
            DataResponse[Optional[User]], QUERY, variables
        ).data

    def update(self, input: UserUpdateInput) -> User:
        QUERY = gql(
            """
            mutation ActiveUserMutations($input: UserUpdateInput!) {
              data:activeUserMutations {
                data:update(user: $input) {
                  id
                  email
                  name
                  bio
                  company
                  avatar
                  verified
                  role
                }
              }
            }
           """
        )

        variables = {"input": input.model_dump(warnings="error", by_alias=True)}

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[User]], QUERY, variables
        ).data.data

    def get_projects(
        self,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[UserProjectsFilter] = None,
    ) -> ResourceCollection[Project]:
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
            DataResponse[Optional[DataResponse[ResourceCollection[Project]]]],
            QUERY,
            variables,
        )

        if response.data is None:
            raise GraphQLException(
                "GraphQL response indicated that the ActiveUser could not be found"
            )

        return response.data.data

    def get_project_invites(self) -> List[PendingStreamCollaborator]:
        QUERY = gql(
            """
            query ProjectInvites {
              data:activeUser {
                data:projectInvites {
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
                    id
                    name
                    bio
                    company
                    verified
                    avatar
                    role
                  }
                }
              }
            }
            """
        )

        variables = {}

        response = self.make_request_and_parse_response(
            DataResponse[Optional[DataResponse[List[PendingStreamCollaborator]]]],
            QUERY,
            variables,
        )

        if response.data is None:
            raise GraphQLException(
                "GraphQL response indicated that the ActiveUser could not be found"
            )

        return response.data.data
