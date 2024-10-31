import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.models import User


@pytest.mark.run()
class TestOtherUserResource:
    @pytest.fixture(scope="class")
    def test_data(self, second_client: SpeckleClient) -> User:
        user_info = second_client.active_user.get()
        assert user_info
        return user_info

    def test_other_user_get(self, client: SpeckleClient, test_data: User):
        res = client.other_user.get(test_data.id)
        assert res is not None
        assert res.name == test_data.name

    def test_other_user_get_non_existent_user(self, client: SpeckleClient):
        result = client.other_user.get("AnIdThatDoesntExist")
        assert result is None

    def test_user_search(self, client: SpeckleClient, test_data: User):
        assert test_data.email
        res = client.other_user.user_search(test_data.email, limit=25)
        assert len(res.items) == 1
        assert res.items[0].id == test_data.id

    def test_user_search_non_existent_user(self, client: SpeckleClient):
        res = client.other_user.user_search("idontexist@example.com", limit=25)
        assert len(res.items) == 0
