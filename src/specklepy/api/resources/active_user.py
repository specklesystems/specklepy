from datetime import datetime, timezone
from typing import List, Optional

from gql import gql

from specklepy.api.models import ActivityCollection, PendingStreamCollaborator, User
from specklepy.api.resource import ResourceBase
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException

from specklepy.core.api.resources.active_user import NAME, Resource as Core_Resource


class Resource(Core_Resource):
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
        metrics.track(metrics.SDK, custom_props={"name": "User Get"})
        
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
        metrics.track(metrics.SDK, self.account, {"name": "User Update"})
        
        return super().update(name, company, bio, avatar)

    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Get all of the active user's pending stream invites

        Requires Speckle Server version >= 2.6.4

        Returns:
            List[PendingStreamCollaborator]
            -- a list of pending invites for the current user
        """
        metrics.track(metrics.SDK, self.account, {"name": "Invite Get"})
        
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
        metrics.track(metrics.SDK, self.account, {"name": "Invite Get"})
        
        return super().get_pending_invite(stream_id, token)
