from datetime import datetime
from typing import List, Optional

from specklepy.api.models import PendingStreamCollaborator, User
from specklepy.core.api.resources.active_user import Resource as CoreResource
from specklepy.logging import metrics


class Resource(CoreResource):
    """API Access class for users. This class provides methods to get and update
    the user profile, fetch user activity, and manage pending stream invitations."""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )
        self.schema = User

    def get(self) -> User:
        """Gets the profile of the current authenticated user's profile
        (as extracted from the authorization header).

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

        Args:
            name (Optional[str]): The user's name.
            company (Optional[str]): The company the user works for.
            bio (Optional[str]): A brief user biography.
            avatar (Optional[str]): A URL to an avatar image for the user.

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
        Fetches collection the current authenticated user's activity
        as filtered by given parameters

        Note: all timestamps arguments should be `datetime` of any tz as they will be
        converted to UTC ISO format strings

        Args:
            limit (int): The maximum number of activity items to return.
            action_type (Optional[str]): Filter results to a single action type.
            before (Optional[datetime]): Latest cutoff for activity to include.
            after (Optional[datetime]): Oldest cutoff for an activity to include.
            cursor (Optional[datetime]): Timestamp cursor for pagination.

        Returns:
            Activity collection, filtered according to the provided parameters.
        """
        metrics.track(metrics.SDK, self.account, {"name": "User Active Activity"})
        return super().activity(limit, action_type, before, after, cursor)

    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Fetches all of the current user's pending stream invitations.

        Returns:
            List[PendingStreamCollaborator]: A list of pending stream invitations.
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "User Active Invites All Get"}
        )
        return super().get_all_pending_invites()

    def get_pending_invite(
        self, stream_id: str, token: Optional[str] = None
    ) -> Optional[PendingStreamCollaborator]:
        """Fetches a specific pending invite for the current user on a given stream.

        Args:
            stream_id (str): The ID of the stream to look for invites on.
            token (Optional[str]): The token of the invite to look for (optional).

        Returns:
            Optional[PendingStreamCollaborator]: The invite for the given stream, or None if not found.
        """
        metrics.track(metrics.SDK, self.account, {"name": "User Active Invite Get"})
        return super().get_pending_invite(stream_id, token)
