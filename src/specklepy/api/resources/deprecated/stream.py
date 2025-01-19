from datetime import datetime
from typing import List, Optional

from deprecated import deprecated

from specklepy.api.models import PendingStreamCollaborator, Stream
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resources.deprecated.stream import Resource as CoreResource
from specklepy.logging import metrics


class Resource(CoreResource):
    """API Access class for streams"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

        self.schema = Stream

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get(self, id: str, branch_limit: int = 10, commit_limit: int = 10) -> Stream:
        """Get the specified stream from the server

        Arguments:
            id {str} -- the stream id
            branch_limit {int} -- the maximum number of branches to return
            commit_limit {int} -- the maximum number of commits to return

        Returns:
            Stream -- the retrieved stream
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Get"})
        return super().get(id, branch_limit, commit_limit)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def list(self, stream_limit: int = 10) -> List[Stream]:
        """Get a list of the user's streams

        Arguments:
            stream_limit {int} -- The maximum number of streams to return

        Returns:
            List[Stream] -- A list of Stream objects
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream List"})
        return super().list(stream_limit)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def create(
        self,
        name: str = "Anonymous Python Stream",
        description: str = "No description provided",
        is_public: bool = True,
    ) -> str:
        """Create a new stream

        Arguments:
            name {str} -- the name of the string
            description {str} -- a short description of the stream
            is_public {bool}
                -- whether or not the stream can be viewed by anyone with the id

        Returns:
            id {str} -- the id of the newly created stream
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Create"})
        return super().create(name, description, is_public)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def update(
        self,
        id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> bool:
        """Update an existing stream

        Arguments:
            id {str} -- the id of the stream to be updated
            name {str} -- the name of the string
            description {str} -- a short description of the stream
            is_public {bool}
                -- whether or not the stream can be viewed by anyone with the id

        Returns:
            bool -- whether the stream update was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Update"})
        return super().update(id, name, description, is_public)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def delete(self, id: str) -> bool:
        """Delete a stream given its id

        Arguments:
            id {str} -- the id of the stream to delete

        Returns:
            bool -- whether the deletion was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Delete"})
        return super().delete(id)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def search(
        self,
        search_query: str,
        limit: int = 25,
        branch_limit: int = 10,
        commit_limit: int = 10,
    ):
        """Search for streams by name, description, or id

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
            branch_limit {int} -- the maximum number of branches to return
            commit_limit {int} -- the maximum number of commits to return

        Returns:
            List[Stream] -- a list of Streams that match the search query
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Search"})
        return super().search(search_query, limit, branch_limit, commit_limit)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def favorite(self, stream_id: str, favorited: bool = True):
        """Favorite or unfavorite the given stream.

        Arguments:
            stream_id {str} -- the id of the stream to favorite / unfavorite
            favorited {bool}
                -- whether to favorite (True) or unfavorite (False) the stream

        Returns:
            Stream -- the stream with its `id`, `name`, and `favoritedDate`
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Favorite"})
        return super().favorite(stream_id, favorited)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get_all_pending_invites(
        self, stream_id: str
    ) -> List[PendingStreamCollaborator]:
        """Get all of the pending invites on a stream.
        You must be a `stream:owner` to query this.

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the stream id from which to get the pending invites

        Returns:
            List[PendingStreamCollaborator]
                -- a list of pending invites for the specified stream
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Invite Get"})
        return super().get_all_pending_invites(stream_id)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def invite(
        self,
        stream_id: str,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        role: str = "stream:contributor",  # should default be reviewer?
        message: Optional[str] = None,
    ):
        """Invite someone to a stream using either their email or user id

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream to invite the user to
            email {str} -- the email of the user to invite (use this OR `user_id`)
            user_id {str} -- the id of the user to invite (use this OR `email`)
            role {str}
                -- the role to assign to the user (defaults to `stream:contributor`)
            message {str}
                -- a message to send along with this invite to the specified user

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Invite Create"})
        return super().invite(stream_id, email, user_id, role, message)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def invite_batch(
        self,
        stream_id: str,
        emails: Optional[List[str]] = None,
        user_ids: Optional[List[None]] = None,
        message: Optional[str] = None,
    ) -> bool:
        """Invite a batch of users to a specified stream.

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream to invite the user to
            emails {List[str]}
                -- the email of the user to invite (use this and/or `user_ids`)
            user_id {List[str]}
                -- the id of the user to invite (use this and/or `emails`)
            message {str}
                -- a message to send along with this invite to the specified user

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Invite Batch Create"})
        return super().invite_batch(stream_id, emails, user_ids, message)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def invite_cancel(self, stream_id: str, invite_id: str) -> bool:
        """Cancel an existing stream invite

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream invite
            invite_id {str} -- the id of the invite to use

        Returns:
            bool -- true if the operation was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Invite Cancel"})
        return super().invite_cancel(stream_id, invite_id)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def invite_use(self, stream_id: str, token: str, accept: bool = True) -> bool:
        """Accept or decline a stream invite

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str}
                -- the id of the stream for which the user has a pending invite
            token {str} -- the token of the invite to use
            accept {bool} -- whether or not to accept the invite (defaults to True)

        Returns:
            bool -- true if the operation was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Invite Use"})
        return super().invite_use(stream_id, token, accept)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def update_permission(self, stream_id: str, user_id: str, role: str):
        """Updates permissions for a user on a given stream

        Valid for Speckle Server >=2.6.4

        Arguments:
            stream_id {str} -- the id of the stream to grant permissions to
            user_id {str} -- the id of the user to grant permissions for
            role {str} -- the role to grant the user

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(
            metrics.SDK,
            self.account,
            {"name": "Stream Permission Update", "role": role},
        )
        return super().update_permission(stream_id, user_id, role)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def revoke_permission(self, stream_id: str, user_id: str):
        """Revoke permissions from a user on a given stream

        Arguments:
            stream_id {str} -- the id of the stream to revoke permissions from
            user_id {str} -- the id of the user to revoke permissions from

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Permission Revoke"})
        return super().revoke_permission(stream_id, user_id)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def activity(
        self,
        stream_id: str,
        action_type: Optional[str] = None,
        limit: int = 20,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        cursor: Optional[datetime] = None,
    ):
        """
        Get the activity from a given stream in an Activity collection.
        Step into the activity `items` for the list of activity.

        Note: all timestamps arguments should be `datetime` of any tz
            as they will be converted to UTC ISO format strings

        stream_id {str} -- the id of the stream to get activity from
        action_type {str}
            -- filter results to a single action type
            (eg: `commit_create` or `commit_receive`)
        limit {int} -- max number of Activity items to return
        before {datetime}
            -- latest cutoff for activity (ie: return all activity _before_ this time)
        after {datetime}
            -- oldest cutoff for activity (ie: return all activity _after_ this time)
        cursor {datetime} -- timestamp cursor for pagination
        """
        metrics.track(metrics.SDK, self.account, {"name": "Stream Activity"})
        return super().activity(stream_id, action_type, limit, before, after, cursor)
