from datetime import datetime

import pytest

from specklepy.api.client import SpeckleClient
from specklepy.api.models import (
    Activity,
    ActivityCollection,
    PendingStreamCollaborator,
    Stream,
    User,
)
from specklepy.logging.exceptions import (
    GraphQLException,
    SpeckleException,
    UnsupportedException,
)


@pytest.mark.run(order=3)
class TestStream:
    @pytest.fixture(scope="session")
    def stream(self):
        return Stream(
            name="a wonderful stream",
            description="a stream created for testing",
            isPublic=True,
        )

    @pytest.fixture(scope="module")
    def updated_stream(
        self,
    ):
        return Stream(
            name="a wonderful updated stream",
            description="an updated stream description for testing",
            isPublic=False,
        )

    @pytest.fixture(scope="module")
    def second_user(self, second_client: SpeckleClient):
        return second_client.user.get()

    def test_stream_create(self, client, stream, updated_stream):
        stream.id = updated_stream.id = client.stream.create(
            name=stream.name,
            description=stream.description,
            is_public=stream.isPublic,
        )

        assert isinstance(stream.id, str)

    def test_stream_get(self, client, stream):
        fetched_stream = client.stream.get(stream.id)

        assert fetched_stream.name == stream.name
        assert fetched_stream.description == stream.description
        assert fetched_stream.isPublic == stream.isPublic

    def test_stream_update(self, client, updated_stream):
        updated = client.stream.update(
            id=updated_stream.id,
            name=updated_stream.name,
            description=updated_stream.description,
            is_public=updated_stream.isPublic,
        )
        fetched_stream = client.stream.get(updated_stream.id)

        assert updated is True
        assert fetched_stream.name == updated_stream.name
        assert fetched_stream.description == updated_stream.description
        assert fetched_stream.isPublic == updated_stream.isPublic

    def test_stream_list(self, client):
        client.stream.create(name="a second wonderful stream")
        client.stream.create(name="a third fantastic stream")

        streams = client.stream.list()

        assert len(streams) >= 3

    def test_stream_search(self, client, updated_stream):
        search_results = client.stream.search(updated_stream.name)

        assert len(search_results) == 1
        assert search_results[0].name == updated_stream.name

    def test_stream_favorite(self, client, stream):
        favorited = client.stream.favorite(stream.id)

        assert isinstance(favorited, Stream)
        assert favorited.favoritedDate is not None

        unfavorited = client.stream.favorite(stream.id, False)
        assert isinstance(favorited, Stream)
        assert unfavorited.favoritedDate is None

    def test_stream_grant_permission(self, client, stream, second_user):
        # deprecated as of Speckle Server 2.6.4
        with pytest.raises(UnsupportedException):
            client.stream.grant_permission(
                stream_id=stream.id,
                user_id=second_user.id,
                role="stream:contributor",
            )

    def test_stream_invite(
        self, client: SpeckleClient, stream: Stream, second_user_dict: dict
    ):
        invited = client.stream.invite(
            stream_id=stream.id,
            email=second_user_dict["email"],
            role="stream:reviewer",
            message="welcome to my stream!",
        )

        assert invited is True

        # fail if no email or id
        with pytest.raises(SpeckleException):
            client.stream.invite(stream_id=stream.id)

    def test_stream_invite_get_all_for_user(
        self, second_client: SpeckleClient, stream: Stream
    ):
        # NOTE: these are user queries, but testing here to contain the flow
        invites = second_client.user.get_all_pending_invites()

        assert isinstance(invites, list)
        assert isinstance(invites[0], PendingStreamCollaborator)
        assert len(invites) == 1

        invite = second_client.user.get_pending_invite(stream_id=stream.id)
        assert isinstance(invite, PendingStreamCollaborator)

    def test_stream_invite_use(self, second_client: SpeckleClient, stream: Stream):
        invite: PendingStreamCollaborator = (
            second_client.user.get_all_pending_invites()[0]
        )

        accepted = second_client.stream.invite_use(
            stream_id=stream.id, token=invite.token
        )

        assert accepted is True

    def test_stream_update_permission(
        self, client: SpeckleClient, stream: Stream, second_user: User
    ):
        updated = client.stream.update_permission(
            stream_id=stream.id, user_id=second_user.id, role="stream:contributor"
        )

        assert updated is True

    def test_stream_revoke_permission(self, client, stream, second_user):
        revoked = client.stream.revoke_permission(
            stream_id=stream.id, user_id=second_user.id
        )

        fetched_stream = client.stream.get(stream.id)

        assert revoked is True
        assert len(fetched_stream.collaborators) == 1

    def test_stream_invite_cancel(
        self,
        client: SpeckleClient,
        stream: Stream,
        second_user: User,
    ):
        invited = client.stream.invite(
            stream_id=stream.id,
            user_id=second_user.id,
            message="welcome to my stream!",
        )
        assert invited is True

        invites = client.stream.get_all_pending_invites(stream_id=stream.id)

        cancelled = client.stream.invite_cancel(
            invite_id=invites[0].inviteId, stream_id=stream.id
        )

        assert cancelled is True

    def test_stream_invite_batch(
        self, client: SpeckleClient, stream: Stream, second_user: User
    ):
        # NOTE: only works for server admins
        # invited = client.stream.invite_batch(
        #     stream_id=stream.id,
        #     emails=["userA@speckle.xyz", "userB@speckle.xyz"],
        #     user_ids=[second_user.id],
        #     message="yeehaw 🤠",
        # )

        # assert invited is True

        # invited_only_email = client.stream.invite_batch(
        #     stream_id=stream.id,
        #     emails=["userC@speckle.xyz"],
        #     message="yeehaw 🤠",
        # )

        # assert invited_only_email is True

        # fail if no emails or user ids
        with pytest.raises(SpeckleException):
            client.stream.invite_batch(stream_id=stream.id)

    def test_stream_activity(self, client: SpeckleClient, stream: Stream):
        activity = client.stream.activity(stream.id)

        older_activity = client.stream.activity(
            stream.id, before=activity.items[0].time
        )

        assert isinstance(activity, ActivityCollection)
        assert isinstance(older_activity, ActivityCollection)
        assert older_activity.totalCount < activity.totalCount
        assert activity.items is not None
        assert isinstance(activity.items[0], Activity)

    def test_stream_delete(self, client, stream):
        deleted = client.stream.delete(stream.id)

        stream_get = client.stream.get(stream.id)

        assert deleted is True
        assert isinstance(stream_get, GraphQLException)
