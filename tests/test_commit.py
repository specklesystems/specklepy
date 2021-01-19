from tests.test_stream import stream
from speckle.api.models import Commit
import pytest


@pytest.fixture(scope="module")
def commit():
    return Commit(message="a fun little test commit")


@pytest.fixture(scope="module")
def updated_commit():
    return Commit(message="a fun little updated commit")


@pytest.fixture(scope="module")
def stream_id(client):
    return client.stream.create("testing commits")


def test_create(client, stream_id, commit):
    commit.id = client.commit.create(
        stream_id=stream_id, object_id="object123", message=commit.message
    )

    assert isinstance(commit.id, str)


def test_get(client, stream_id, commit):
    fetched_commit = client.commit.get(stream_id=stream_id, commit_id=commit.id)

    assert fetched_commit.message == commit.message


def test_update(client, stream_id, commit, updated_commit):
    updated = client.commit.update(
        stream_id=stream_id, commit_id=commit.id, message=updated_commit.message
    )

    fetched_commit = client.commit.get(stream_id=stream_id, commit_id=commit.id)

    assert updated == True
    assert fetched_commit.message == updated_commit.message
