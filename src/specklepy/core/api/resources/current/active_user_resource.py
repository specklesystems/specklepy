from datetime import datetime, timezone
from typing import List, Optional, overload

from deprecated import deprecated
from gql import gql

from specklepy.core.api.inputs.project_inputs import UserProjectsFilter
from specklepy.core.api.inputs.user_inputs import UserUpdateInput
from specklepy.core.api.models import (
    ActivityCollection,
    PendingStreamCollaborator,
    Project,
    ResourceCollection,
    User,
)
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
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
        """Gets the currently active user profile (as extracted from the authorization header)

        Returns:
            User -- the requested user, or none if no authentication token is provided to the Client
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

    def _update(self, input: UserUpdateInput) -> User:
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

        variables = {"input": input.model_dump(warnings="error")}

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[User]], QUERY, variables
        ).data.data

    @deprecated("Use UserUpdateInput overload", version=FE1_DEPRECATION_VERSION)
    @overload
    def update(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        bio: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> User:
        ...

    @overload
    def update(self, *, input: UserUpdateInput) -> User:
        ...

    def update(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        bio: Optional[str] = None,
        avatar: Optional[str] = None,
        *,
        input: Optional[UserUpdateInput] = None,
    ) -> User:
        if isinstance(input, UserUpdateInput):
            return self._update(input=input)
        else:
            return self._update(
                input=UserUpdateInput(
                    name=name,
                    company=company,
                    bio=bio,
                    avatar=avatar,
                )
            )

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
            "filter": filter.model_dump(warnings="error") if filter else None,
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def activity(
        self,
        limit: int = 20,
        action_type: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        cursor: Optional[datetime] = None,
    ) -> ActivityCollection:
        """
        Get the activity from a given stream in an Activity collection.
        Step into the activity `items` for the list of activity.
        If no id argument is provided, will return the current authenticated user's
        activity (as extracted from the authorization header).

        Note: all timestamps arguments should be `datetime` of any tz as they will be
        converted to UTC ISO format strings

        user_id {str} -- the id of the user to get the activity from
        action_type {str} -- filter results to a single action type
            (eg: `commit_create` or `commit_receive`)
        limit {int} -- max number of Activity items to return
        before {datetime} -- latest cutoff for activity
            (ie: return all activity _before_ this time)
        after {datetime} -- oldest cutoff for activity
            (ie: return all activity _after_ this time)
        cursor {datetime} -- timestamp cursor for pagination
        """

        query = gql(
            """
            query UserActivity(
                $action_type: String,
                $before:DateTime,
                $after: DateTime,
                $cursor: DateTime,
                $limit: Int
                ){
                activeUser {
                    activity(
                        actionType: $action_type,
                        before: $before,
                        after: $after,
                        cursor: $cursor,
                        limit: $limit
                        ) {
                        totalCount
                        cursor
                        items {
                            actionType
                            info
                            userId
                            streamId
                            resourceId
                            resourceType
                            message
                            time
                        }
                    }
                }
            }
            """
        )

        params = {
            "limit": limit,
            "action_type": action_type,
            "before": before.astimezone(timezone.utc).isoformat() if before else before,
            "after": after.astimezone(timezone.utc).isoformat() if after else after,
            "cursor": cursor.astimezone(timezone.utc).isoformat() if cursor else cursor,
        }

        return self.make_request(
            query=query,
            params=params,
            return_type=["activeUser", "activity"],
            schema=ActivityCollection,
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Get all of the active user's pending stream invites

        Requires Speckle Server version >= 2.6.4

        Returns:
            List[PendingStreamCollaborator]
            -- a list of pending invites for the current user
        """
        self._check_invites_supported()

        query = gql(
            """
            query StreamInvites {
                streamInvites{
                    id
                    token
                    inviteId
                    streamId
                    streamName
                    projectId
                    projectName
                    title
                    role
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
            """
        )

        return self.make_request(
            query=query,
            return_type="streamInvites",
            schema=PendingStreamCollaborator,
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get_pending_invite(
        self, stream_id: str, token: Optional[str] = None
    ) -> Optional[PendingStreamCollaborator]:
        """Get a particular pending invite for the active user on a given stream.
        If no invite_id is provided, any valid invite will be returned.

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream to look for invites on
            token {str} -- the token of the invite to look for (optional)

        Returns:
            PendingStreamCollaborator
            -- the invite for the given stream (or None if it isn't found)
        """
        self._check_invites_supported()

        query = gql(
            """
            query StreamInvite($streamId: String!, $token: String) {
                streamInvite(streamId: $streamId, token: $token) {
                    id
                    token
                    inviteId
                    streamId
                    streamName
                    projectId
                    projectName
                    title
                    role
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
            """
        )

        params = {"streamId": stream_id}
        if token:
            params["token"] = token

        return self.make_request(
            query=query,
            params=params,
            return_type="streamInvite",
            schema=PendingStreamCollaborator,
        )
