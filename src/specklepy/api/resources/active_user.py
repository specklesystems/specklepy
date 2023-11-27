from datetime import datetime
from typing import List, Optional

from specklepy.api.models import PendingStreamCollaborator, User
from specklepy.core.api.resources.active_user import Resource as CoreResource
from specklepy.logging import metrics


class Resource(CoreResource):
    """API Access class for users"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
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
        metrics.track(metrics.SDK, custom_props={"name": "User Active Get"})
        return super().get()

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
        metrics.track(metrics.SDK, self.account, {"name": "User Active Update"})
        return super().update(name, company, bio, avatar)

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
        metrics.track(metrics.SDK, self.account, {"name": "User Active Activity"})
        return super().activity(limit, action_type, before, after, cursor)

    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Get all of the active user's pending stream invites

        Requires Speckle Server version >= 2.6.4

        Returns:
            List[PendingStreamCollaborator]
            -- a list of pending invites for the current user
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "User Active Invites All Get"}
        )
        return super().get_all_pending_invites()

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
        metrics.track(metrics.SDK, self.account, {"name": "User Active Invite Get"})
        return super().get_pending_invite(stream_id, token)
