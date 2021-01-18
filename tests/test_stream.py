from speckle.logging.exceptions import GraphQLException
import pytest
from speckle.api.models import Stream


@pytest.fixture(scope="module")
def stream():
    return Stream(
        name="a wonderful stream",
        description="a stream created for testing",
        isPublic=True,
    )


@pytest.fixture(scope="module")
def updated_stream():
    return Stream(
        name="a wonderful updated stream",
        description="an updated stream description for testing",
        isPublic=False,
    )


def test_create(client, stream):
    stream_id = client.stream.create(
        name=stream.name,
        description=stream.description,
        is_public=stream.isPublic,
    )
    stream.id = stream_id

    assert isinstance(stream_id, str)


def test_get(client, stream):
    stream = client.stream.get(stream.id)

    assert stream.name == stream.name
    assert stream.description == stream.description
    assert stream.isPublic == stream.isPublic


def test_update(client, stream, updated_stream):
    updated = client.stream.update(
        id=stream.id,
        name=updated_stream.name,
        description=updated_stream.description,
        is_public=updated_stream.isPublic,
    )
    fetched_stream = client.stream.get(stream.id)

    assert updated == True
    assert fetched_stream.name == updated_stream.name
    assert fetched_stream.description == updated_stream.description
    assert fetched_stream.isPublic == updated_stream.isPublic


def test_list(client):
    client.stream.create(name="a second wonderful stream")
    client.stream.create(name="a third fantastic stream")

    streams = client.stream.list()

    assert len(streams) >= 3


def test_search(client, updated_stream):
    search_results = client.stream.search(updated_stream.name)

    assert len(search_results) == 1
    assert search_results[0].name == updated_stream.name


def test_delete(client, stream):
    deleted = client.stream.delete(stream.id)

    stream_get = client.stream.get(stream.id)

    assert deleted == True
    assert isinstance(stream_get, GraphQLException)