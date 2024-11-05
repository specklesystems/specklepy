from datetime import datetime
from typing import List, Optional, overload

from deprecated import deprecated

from specklepy.core.api.inputs.project_inputs import UserProjectsFilter
from specklepy.core.api.inputs.user_inputs import UserUpdateInput
from specklepy.core.api.models import (
    PendingStreamCollaborator,
    Project,
    ResourceCollection,
    User,
)
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resources import ActiveUserResource as CoreResource
from specklepy.logging import metrics


class ActiveUserResource(CoreResource):
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

    def get(self) -> Optional[User]:
        metrics.track(metrics.SDK, self.account, {"name": "Active User Get"})
        return super().get()

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
        metrics.track(metrics.SDK, self.account, {"name": "Active User Update"})
        if isinstance(input, UserUpdateInput):
            return super()._update(input=input)
        else:
            return super()._update(
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
        metrics.track(metrics.SDK, self.account, {"name": "Active User Get Projects"})
        return super().get_projects(limit=limit, cursor=cursor, filter=filter)

    def get_project_invites(self) -> List[PendingStreamCollaborator]:
        metrics.track(
            metrics.SDK, self.account, {"name": "Active User Get Project Invites"}
        )
        return super().get_project_invites()

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get_all_pending_invites(self) -> List[PendingStreamCollaborator]:
        """Fetches all of the current user's pending stream invitations.

        Returns:
            List[PendingStreamCollaborator]: A list of pending stream invitations.
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "User Active Invites All Get"}
        )
        return super().get_all_pending_invites()

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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
