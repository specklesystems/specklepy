from datetime import datetime
from typing import List, Optional, Union

from deprecated import deprecated

from specklepy.api.models import PendingStreamCollaborator, User
from specklepy.core.api.resources.deprecated.user import Resource as CoreResource
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException

DEPRECATION_VERSION = "2.9.0"
DEPRECATION_TEXT = (
    "The user resource is deprecated, please use the active_user or other_user"
    " resources"
)


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

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
    def get(self, id: Optional[str] = None) -> User:
        """
        Gets the profile of a user.
        If no id argument is provided, will return the current authenticated
        user's profile (as extracted from the authorization header).

        Arguments:
            id {str} -- the user id

        Returns:
            User -- the retrieved user
        """
        metrics.track(metrics.SDK, self.account, {"name": "User Get_deprecated"})
        return super().get(id)

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
    def search(
        self, search_query: str, limit: int = 25
    ) -> Union[List[User], SpeckleException]:
        """
        Searches for user by name or email.
        The search query must be at least 3 characters long

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
        Returns:
            List[User] -- a list of User objects that match the search query
        """
        metrics.track(metrics.SDK, self.account, {"name": "User Search_deprecated"})
        return super().search(search_query, limit)

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
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

        Returns:
            bool -- True if your profile was updated successfully
        """
        # metrics.track(metrics.USER, self.account, {"name": "update"})
        metrics.track(metrics.SDK, self.account, {"name": "User Update_deprecated"})
        return super().update(name, company, bio, avatar)

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
    def activity(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        action_type: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        cursor: Optional[datetime] = None,
    ):
        """
        Get the activity from a given stream in an Activity collection.
        Step into the activity `items` for the list of activity.
        If no id argument is provided, will return the current authenticated
        user's activity (as extracted from the authorization header).

        Note: all timestamps arguments should be `datetime` of any tz as
        they will be converted to UTC ISO format strings

        user_id {str} -- the id of the user to get the activity from
        action_type {str} -- filter results to a single action type
        (eg: `commit_create` or `commit_receive`)
        limit {int} -- max number of Activity items to return
        before {datetime}
            -- latest cutoff for activity (ie: return all activity _before_ this time)
        after {datetime}
            -- oldest cutoff for activity (ie: return all activity _after_ this time)
        cursor {datetime} -- timestamp cursor for pagination
        """
        metrics.track(metrics.SDK, self.account, {"name": "User Activity_deprecated"})
        return super().activity(user_id, limit, action_type, before, after, cursor)

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Get all of the active user's pending stream invites

        Requires Speckle Server version >= 2.6.4

        Returns:
            List[PendingStreamCollaborator]
                -- a list of pending invites for the current user
        """
        # metrics.track(metrics.INVITE, self.account, {"name": "get"})
        metrics.track(
            metrics.SDK, self.account, {"name": "User GetAllInvites_deprecated"}
        )
        return super().get_all_pending_invites()

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_TEXT)
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
        # metrics.track(metrics.INVITE, self.account, {"name": "get"})
        metrics.track(metrics.SDK, self.account, {"name": "User GetInvite_deprecated"})
        return super().get_pending_invite(stream_id, token)
