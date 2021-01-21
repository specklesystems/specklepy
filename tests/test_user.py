from speckle.logging.exceptions import SpeckleException
from speckle.api.models import User
import pytest


@pytest.mark.run(order=1)
class TestUser:
    def test_user_get_self(self, client, user_dict):
        fetched_user = client.user.get()

        assert isinstance(fetched_user, User)
        assert fetched_user.name == user_dict["name"]
        assert fetched_user.email == user_dict["email"]

        user_dict["id"] = fetched_user.id

    def test_user_search(self, client, second_user_dict):
        search_results = client.user.search(search_query=second_user_dict["name"][:5])

        assert isinstance(search_results, list)
        assert isinstance(search_results[0], User)
        assert search_results[0].name == second_user_dict["name"]

        second_user_dict["id"] = search_results[0].id

    def test_user_get(self, client, second_user_dict):
        fetched_user = client.user.get(id=second_user_dict["id"])

        assert isinstance(fetched_user, User)
        assert fetched_user.name == second_user_dict["name"]
        assert fetched_user.email == second_user_dict["email"]

        second_user_dict["id"] = fetched_user.id

    def test_user_update(self, client):
        bio = "i am a ghost in the machine"

        failed_update = client.user.update()
        updated = client.user.update(bio=bio)

        me = client.user.get()

        assert isinstance(failed_update, SpeckleException)
        assert updated is True
        assert me.bio == bio