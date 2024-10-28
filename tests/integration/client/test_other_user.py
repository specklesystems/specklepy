import pytest
from deprecated import deprecated

from specklepy.api.client import SpeckleClient
from specklepy.api.models import Activity, ActivityCollection, LimitedUser


@deprecated()
@pytest.mark.run(order=4)
class TestOtherUser:
    def test_user_get_self(self, client):
        """
        Test, that a limited user query cannot query the active user.
        """
        with pytest.raises(TypeError):
            client.other_user.get()

    def test_user_search(self, client, second_user_dict):
        search_results = client.other_user.search(
            search_query=second_user_dict["name"][:5]
        )

        assert isinstance(search_results, list)
        assert len(search_results) > 0
        result_user = search_results[0]
        assert isinstance(result_user, LimitedUser)
        assert result_user.name == second_user_dict["name"]

        second_user_dict["id"] = result_user.id
        assert getattr(result_user, "email", None) is None

    def test_user_get(self, client, second_user_dict):
        fetched_user = client.other_user.get(id=second_user_dict["id"])

        assert isinstance(fetched_user, LimitedUser)
        assert fetched_user.name == second_user_dict["name"]
        # changed in the server, now you cannot get emails of other users
        # not checking this, since the first user could or could not be an admin on the server
        # admins can get emails of others, regular users can't
        # assert fetched_user.email == None

        second_user_dict["id"] = fetched_user.id

    def test_user_activity(self, client: SpeckleClient, second_user_dict):
        their_activity = client.other_user.activity(second_user_dict["id"])

        assert isinstance(their_activity, ActivityCollection)
        assert isinstance(their_activity.items, list)
        assert isinstance(their_activity.items[0], Activity)
        assert their_activity.totalCount
        assert their_activity.totalCount > 0
