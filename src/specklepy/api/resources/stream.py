from datetime import datetime, timezone
from typing import List, Optional

from deprecated import deprecated
from gql import gql

from specklepy.api.models import ActivityCollection, PendingStreamCollaborator, Stream
from specklepy.api.resource import ResourceBase
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException, UnsupportedException

NAME = "stream"


class Resource(ResourceBase):
    """API Access class for streams"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

        self.schema = Stream

    def get(self, id: str, branch_limit: int = 10, commit_limit: int = 10) -> Stream:
        """Get the specified stream from the server

        Arguments:
            id {str} -- the stream id
            branch_limit {int} -- the maximum number of branches to return
            commit_limit {int} -- the maximum number of commits to return

        Returns:
            Stream -- the retrieved stream
        """
        metrics.track(metrics.STREAM, self.account, {"name": "get"})
        query = gql(
            """
            query Stream($id: String!, $branch_limit: Int!, $commit_limit: Int!) {
                stream(id: $id) {
                    id
                    name
                    role
                    description
                    isPublic
                    createdAt
                    updatedAt
                    commentCount
                    favoritesCount
                    collaborators {
                        id
                        name
                        role
                        avatar
                    }
                    branches(limit: $branch_limit) {
                        totalCount
                        cursor
                        items {
                            id
                            name
                            description
                            commits(limit: $commit_limit) {
                                totalCount
                                cursor
                                items {
                                    id
                                    message
                                    authorId
                                    createdAt
                                    authorName
                                    referencedObject
                                    sourceApplication
                                }
                              }
                          }
                      }
                }
            }
          """
        )

        params = {"id": id, "branch_limit": branch_limit, "commit_limit": commit_limit}

        return self.make_request(query=query, params=params, return_type="stream")

    def list(self, stream_limit: int = 10) -> List[Stream]:
        """Get a list of the user's streams

        Arguments:
            stream_limit {int} -- The maximum number of streams to return

        Returns:
            List[Stream] -- A list of Stream objects
        """
        metrics.track(metrics.STREAM, self.account, {"name": "get"})
        query = gql(
            """
            query User($stream_limit: Int!) {
                user {
                    id
                    bio
                    name
                    email
                    avatar
                    company
                    verified
                    profiles
                    role
                    streams(limit: $stream_limit) {
                        totalCount
                        cursor
                        items {
                            id
                            name
                            role
                            isPublic
                            createdAt
                            updatedAt
                            description
                            commentCount
                            favoritesCount
                            collaborators {
                                id
                                name
                                role
                            }
                          }
                      }
                  }
            }
          """
        )

        params = {"stream_limit": stream_limit}

        return self.make_request(
            query=query, params=params, return_type=["user", "streams", "items"]
        )

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
        metrics.track(metrics.STREAM, self.account, {"name": "create"})
        query = gql(
            """
            mutation StreamCreate($stream: StreamCreateInput!) {
              streamCreate(stream: $stream)
            }
        """
        )

        params = {
            "stream": {"name": name, "description": description, "isPublic": is_public}
        }

        return self.make_request(
            query=query, params=params, return_type="streamCreate", parse_response=False
        )

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
        metrics.track(metrics.STREAM, self.account, {"name": "update"})
        query = gql(
            """
            mutation StreamUpdate($stream: StreamUpdateInput!) {
                streamUpdate(stream: $stream)
            }
        """
        )

        params = {
            "id": id,
            "name": name,
            "description": description,
            "isPublic": is_public,
        }
        # remove None values so graphql doesn't cry
        params = {"stream": {k: v for k, v in params.items() if v is not None}}

        return self.make_request(
            query=query, params=params, return_type="streamUpdate", parse_response=False
        )

    def delete(self, id: str) -> bool:
        """Delete a stream given its id

        Arguments:
            id {str} -- the id of the stream to delete

        Returns:
            bool -- whether the deletion was successful
        """
        metrics.track(metrics.STREAM, self.account, {"name": "delete"})
        query = gql(
            """
            mutation StreamDelete($id: String!) {
                streamDelete(id: $id)
            }
            """
        )

        params = {"id": id}

        return self.make_request(
            query=query, params=params, return_type="streamDelete", parse_response=False
        )

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
        metrics.track(metrics.STREAM, self.account, {"name": "search"})
        query = gql(
            """
            query StreamSearch(
                $search_query: String!,
                $limit: Int!,
                $branch_limit:Int!,
                $commit_limit:Int!
            ) {
                streams(query: $search_query, limit: $limit) {
                    items {
                        id
                        name
                        role
                        description
                        isPublic
                        createdAt
                        updatedAt
                        collaborators {
                            id
                            name
                            role
                            avatar
                        }
                        branches(limit: $branch_limit) {
                            totalCount
                            cursor
                            items {
                                id
                                name
                                description
                                commits(limit: $commit_limit) {
                                    totalCount
                                    cursor
                                    items {
                                        id
                                        referencedObject
                                        message
                                        authorName
                                        authorId
                                        createdAt
                                    }
                                }
                            }
                        }
                    }
                }
            }
          """
        )

        params = {
            "search_query": search_query,
            "limit": limit,
            "branch_limit": branch_limit,
            "commit_limit": commit_limit,
        }

        return self.make_request(
            query=query, params=params, return_type=["streams", "items"]
        )

    def favorite(self, stream_id: str, favorited: bool = True):
        """Favorite or unfavorite the given stream.

        Arguments:
            stream_id {str} -- the id of the stream to favorite / unfavorite
            favorited {bool}
                -- whether to favorite (True) or unfavorite (False) the stream

        Returns:
            Stream -- the stream with its `id`, `name`, and `favoritedDate`
        """
        metrics.track(metrics.STREAM, self.account, {"name": "favorite"})
        query = gql(
            """
            mutation StreamFavorite($stream_id: String!, $favorited: Boolean!) {
                streamFavorite(streamId: $stream_id, favorited: $favorited) {
                    id
                    name
                    favoritedDate
                    favoritesCount
                }
            }
            """
        )

        params = {
            "stream_id": stream_id,
            "favorited": favorited,
        }

        return self.make_request(
            query=query, params=params, return_type=["streamFavorite"]
        )

    @deprecated(
        version="2.6.4",
        reason=(
            "As of Speckle Server v2.6.4, this method is deprecated. Users need to be"
            " invited and accept the invite before being added to a stream"
        ),
    )
    def grant_permission(self, stream_id: str, user_id: str, role: str):
        """Grant permissions to a user on a given stream

        Valid for Speckle Server version < 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream to grant permissions to
            user_id {str} -- the id of the user to grant permissions for
            role {str} -- the role to grant the user

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(metrics.PERMISSION, self.account, {"name": "add", "role": role})
        # we're checking for the actual version info, and if the version is 'dev' we treat it
        # as an up to date instance
        if self.server_version and (
            self.server_version == ("dev",) or self.server_version >= (2, 6, 4)
        ):
            raise UnsupportedException(
                "Server mutation `grant_permission` is no longer supported as of"
                " Speckle Server v2.6.4. Please use the new `update_permission` method"
                " to change an existing user's permission or use the `invite` method to"
                " invite a user to a stream."
            )

        query = gql(
            """
            mutation StreamGrantPermission(
                $permission_params: StreamGrantPermissionInput !
                ) {
                streamGrantPermission(permissionParams: $permission_params)
            }
            """
        )

        params = {
            "permission_params": {
                "streamId": stream_id,
                "userId": user_id,
                "role": role,
            }
        }

        return self.make_request(
            query=query,
            params=params,
            return_type="streamGrantPermission",
            parse_response=False,
        )

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
        metrics.track(metrics.INVITE, self.account, {"name": "get"})
        self._check_invites_supported()

        query = gql(
            """
            query StreamInvites($streamId: String!) {
                stream(id: $streamId){
                    pendingCollaborators {
                        id
                        token
                        inviteId
                        streamId
                        streamName
                        title
                        role
                        invitedBy{
                            id
                            name
                            company
                            avatar
                        }
                        user {
                            id
                            name
                            company
                            avatar
                        }
                    }
                }
            }
            """
        )
        params = {"streamId": stream_id}

        return self.make_request(
            query=query,
            params=params,
            return_type=["stream", "pendingCollaborators"],
            schema=PendingStreamCollaborator,
        )

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
        metrics.track(metrics.INVITE, self.account, {"name": "create"})
        self._check_invites_supported()

        if email is None and user_id is None:
            raise SpeckleException(
                "You must provide either an email or a user id to use the"
                " `stream.invite` method"
            )

        query = gql(
            """
            mutation StreamInviteCreate($input: StreamInviteCreateInput!) {
                streamInviteCreate(input: $input)
            }
            """
        )

        params = {
            "email": email,
            "userId": user_id,
            "streamId": stream_id,
            "message": message,
            "role": role,
        }
        params = {"input": {k: v for k, v in params.items() if v is not None}}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamInviteCreate",
            parse_response=False,
        )

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
        metrics.track(metrics.INVITE, self.account, {"name": "batch create"})
        self._check_invites_supported()
        if emails is None and user_ids is None:
            raise SpeckleException(
                "You must provide either an email or a user id to use the"
                " `stream.invite` method"
            )

        query = gql(
            """
            mutation StreamInviteBatchCreate($input: [StreamInviteCreateInput!]!) {
                streamInviteBatchCreate(input: $input)
            }
            """
        )

        email_invites = [
            {"streamId": stream_id, "message": message, "email": email}
            for email in emails
            if emails is not None
        ]

        user_invites = [
            {"streamId": stream_id, "message": message, "userId": user_id}
            for user_id in user_ids
            if user_ids is not None
        ]

        params = {"input": [*email_invites, *user_invites]}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamInviteBatchCreate",
            parse_response=False,
        )

    def invite_cancel(self, stream_id: str, invite_id: str) -> bool:
        """Cancel an existing stream invite

        Requires Speckle Server version >= 2.6.4

        Arguments:
            stream_id {str} -- the id of the stream invite
            invite_id {str} -- the id of the invite to use

        Returns:
            bool -- true if the operation was successful
        """
        metrics.track(metrics.INVITE, self.account, {"name": "cancel"})
        self._check_invites_supported()

        query = gql(
            """
            mutation StreamInviteCancel($streamId: String!, $inviteId: String!) {
                streamInviteCancel(streamId: $streamId, inviteId: $inviteId)
            }
            """
        )

        params = {"streamId": stream_id, "inviteId": invite_id}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamInviteCancel",
            parse_response=False,
        )

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
        metrics.track(metrics.INVITE, self.account, {"name": "use"})
        self._check_invites_supported()

        query = gql(
            """
            mutation StreamInviteUse(
                $accept: Boolean!,
                $streamId: String!,
                $token: String!
                ) {
                streamInviteUse(accept: $accept, streamId: $streamId, token: $token)
            }
            """
        )

        params = {"streamId": stream_id, "token": token, "accept": accept}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamInviteUse",
            parse_response=False,
        )

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
            metrics.PERMISSION, self.account, {"name": "update", "role": role}
        )
        if self.server_version and (
            self.server_version != ("dev",) and self.server_version < (2, 6, 4)
        ):
            raise UnsupportedException(
                "Server mutation `update_permission` is only supported as of Speckle"
                " Server v2.6.4. Please update your Speckle Server to use this method"
                " or use the `grant_permission` method instead."
            )
        query = gql(
            """
            mutation StreamUpdatePermission(
                $permission_params: StreamUpdatePermissionInput!
                ) {
                streamUpdatePermission(permissionParams: $permission_params)
            }
            """
        )

        params = {
            "permission_params": {
                "streamId": stream_id,
                "userId": user_id,
                "role": role,
            }
        }

        return self.make_request(
            query=query,
            params=params,
            return_type="streamUpdatePermission",
            parse_response=False,
        )

    def revoke_permission(self, stream_id: str, user_id: str):
        """Revoke permissions from a user on a given stream

        Arguments:
            stream_id {str} -- the id of the stream to revoke permissions from
            user_id {str} -- the id of the user to revoke permissions from

        Returns:
            bool -- True if the operation was successful
        """
        metrics.track(metrics.PERMISSION, self.account, {"name": "revoke"})
        query = gql(
            """
            mutation StreamRevokePermission(
                $permission_params: StreamRevokePermissionInput!
                ) {
                streamRevokePermission(permissionParams: $permission_params)
            }
            """
        )

        params = {"permission_params": {"streamId": stream_id, "userId": user_id}}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamRevokePermission",
            parse_response=False,
        )

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
        query = gql(
            """
            query StreamActivity(
                $stream_id: String!,
                $action_type: String,
                $before:DateTime,
                $after: DateTime,
                $cursor: DateTime,
                $limit: Int
                ){
                stream(id: $stream_id) {
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
        try:
            params = {
                "stream_id": stream_id,
                "limit": limit,
                "action_type": action_type,
                "before": before.astimezone(timezone.utc).isoformat()
                if before
                else before,
                "after": after.astimezone(timezone.utc).isoformat() if after else after,
                "cursor": cursor.astimezone(timezone.utc).isoformat()
                if cursor
                else cursor,
            }
        except AttributeError as e:
            raise SpeckleException(
                "Could not get stream activity - `before`, `after`, and `cursor` must"
                " be in `datetime` format if provided",
                ValueError(),
            ) from e

        return self.make_request(
            query=query,
            params=params,
            return_type=["stream", "activity"],
            schema=ActivityCollection,
        )
