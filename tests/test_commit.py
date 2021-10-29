import pytest
from specklepy.api import operations
from specklepy.api.models import Commit, Stream
from specklepy.transports.server.server import ServerTransport


@pytest.mark.run(order=4)
class TestCommit:
    @pytest.fixture(scope="module")
    def commit(self):
        return Commit(message="a fun little test commit")

    @pytest.fixture(scope="module")
    def updated_commit(
        self,
    ):
        return Commit(message="a fun little updated commit")

    @pytest.fixture(scope="module")
    def stream(self, client):
        stream = Stream(
            name="a sample stream for testing",
            description="a stream created for testing",
            isPublic=True,
        )
        stream.id = client.stream.create(
            stream.name, stream.description, stream.isPublic
        )
        return stream

    def test_commit_create(self, client, stream, mesh, commit):
        transport = ServerTransport(client=client, stream_id=stream.id)
        mesh.id = operations.send(mesh, transports=[transport])

        commit.id = client.commit.create(
            stream_id=stream.id, object_id=mesh.id, message=commit.message
        )

        assert isinstance(commit.id, str)

    def test_commit_get(self, client, stream, mesh, commit):
        fetched_commit = client.commit.get(stream_id=stream.id, commit_id=commit.id)

        assert fetched_commit.message == commit.message
        assert fetched_commit.referencedObject == mesh.id

    def test_commit_list(self, client, stream):
        commits = client.commit.list(stream_id=stream.id)

        assert isinstance(commits, list)
        assert isinstance(commits[0], Commit)

    def test_commit_update(self, client, stream, commit, updated_commit):
        updated = client.commit.update(
            stream_id=stream.id, commit_id=commit.id, message=updated_commit.message
        )

        fetched_commit = client.commit.get(stream_id=stream.id, commit_id=commit.id)

        assert updated is True
        assert fetched_commit.message == updated_commit.message

    def test_commit_delete(self, client, stream, mesh):
        commit_id = client.commit.create(
            stream_id=stream.id, object_id=mesh.id, message="a great commit to delete"
        )

        deleted = client.commit.delete(stream_id=stream.id, commit_id=commit_id)

        assert deleted is True

    def test_commit_marked_as_received(self, client, stream, mesh) -> None:
        commit = Commit(message="this commit should be received")
        commit.id = client.commit.create(
            stream_id=stream.id,
            object_id=mesh.id,
            message=commit.message,
        )

        commit_marked_received = client.commit.received(
            stream.id,
            commit.id,
            source_application="pytest",
            message="testing received",
        )

        assert commit_marked_received == True
