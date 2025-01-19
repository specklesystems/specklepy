import pytest

from specklepy.api.client import SpeckleClient
from specklepy.api.models import Activity, ActivityCollection, User
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run(order=2)
class TestUser:
    def test_user_get_self(self, client: SpeckleClient, user_dict):
        fetched_user = client.active_user.get()

        assert isinstance(fetched_user, User)
        assert fetched_user.name == user_dict["name"]
        assert fetched_user.email == user_dict["email"]

        user_dict["id"] = fetched_user.id

    def test_user_update(self, client: SpeckleClient):
        bio = "i am a ghost in the machine"

        with pytest.raises(GraphQLException):
            client.active_user.update(bio=None)

        updated = client.active_user.update(bio=bio)

        assert isinstance(updated, User)
        assert isinstance(updated, User)
        assert updated.bio == bio

    def test_user_activity(self, client: SpeckleClient, second_user_dict):
        my_activity = client.active_user.activity(limit=10)
        their_activity = client.other_user.activity(second_user_dict["id"])

        assert isinstance(my_activity, ActivityCollection)
        assert my_activity.items
        assert isinstance(my_activity.items[0], Activity)
        assert my_activity.totalCount
        assert isinstance(their_activity, ActivityCollection)

        older_activity = client.active_user.activity(before=my_activity.items[0].time)

        assert isinstance(older_activity, ActivityCollection)
        assert older_activity.totalCount
        assert older_activity.totalCount < my_activity.totalCount
