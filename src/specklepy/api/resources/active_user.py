from datetime import datetime, timezone
from typing import List, Optional

from gql import gql

from specklepy.api.models import ActivityCollection, PendingStreamCollaborator, User
from specklepy.api.resource import ResourceBase
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException

NAME = "active_user"


class Resource(ResourceBase):
    """API Access class for users"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )
        self.schema = User

    def get(self) -> User:
        """Gets the profile of a user. If no id argument is provided,
        will return the current authenticated user's profile
        (as extracted from the authorization header).

        Arguments:
            id {str} -- the user id

        Returns:
            User -- the retrieved user
        """
        metrics.track(metrics.USER, self.account, {"name": "get"})
        query = gql(
            """
            query User {
                activeUser {
                    id
                    email
                    name
                    bio
                    company
                    avatar
                    verified
                    profiles
                    role
                }
            }
          """
        )

        params = {}

        return self.make_request(query=query, params=params, return_type="activeUser")

    def update(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        bio: Optional[str] = None,
        avatar: Optional[str] = None,
    ):
        """Updates your user profile. All arguments are optional.

        Arguments:
            name {str} -- your name
            company {str} -- the company you may or may not work for
            bio {str} -- tell us about yourself
            avatar {str} -- a nice photo of yourself

        Returns    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT):
            bool -- True if your profile was updated successfully
        """
        metrics.track(metrics.USER, self.account, {"name": "update"})
        query = gql(
            """
            mutation UserUpdate($user: UserUpdateInput!) {
                userUpdate(user: $user)
            }
            """
        )
        params = {"name": name, "company": company, "bio": bio, "avatar": avatar}

        params = {"user": {k: v for k, v in params.items() if v is not None}}

        if not params["user"]:
            return SpeckleException(
                message=(
                    "You must provide at least one field to update your user profile"
                )
            )

        return self.make_request(
            query=query, params=params, return_type="userUpdate", parse_response=False
        )

    def activity(
        self,
        limit: int = 20,
        action_type: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        cursor: Optional[datetime] = None,
    ):
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

    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Get all of the active user's pending stream invites

        Requires Speckle Server version >= 2.6.4

        Returns:
            List[PendingStreamCollaborator]
            -- a list of pending invites for the current user
        """
        metrics.track(metrics.INVITE, self.account, {"name": "get"})
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
                    title
                    role
                    invitedBy {
                        id
                        name
                        company
                        avatar
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
        metrics.track(metrics.INVITE, self.account, {"name": "get"})
        self._check_invites_supported()

        query = gql(
            """
            query StreamInvite($streamId: String!, $token: String) {
                streamInvite(streamId: $streamId, token: $token) {
                    id
                    token
                    streamId
                    streamName
                    title
                    role
                    invitedBy {
                        id
                        name
                        company
                        avatar
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
