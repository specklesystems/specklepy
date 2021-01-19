import pytest
from speckle.api.models import Stream
from speckle.logging.exceptions import GraphQLException


@pytest.mark.run(order=1)
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

    def test_stream_delete(self, client, stream):
        deleted = client.stream.delete(stream.id)

        stream_get = client.stream.get(stream.id)

        assert deleted is True
        assert isinstance(stream_get, GraphQLException)
