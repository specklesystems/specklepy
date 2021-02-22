from speckle.api.models import Branch, Commit, Stream
import pytest


class TestBranch:
    @pytest.fixture(scope="module")
    def branch(self):
        return Branch(name="olive branch 🌿", description="a test branch")

    @pytest.fixture(scope="module")
    def updated_branch(self):
        return Branch(name="eucalyptus branch 🌿", description="an updated test branch")

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

    def test_branch_create(self, client, stream, branch):
        branch.id = client.branch.create(
            stream_id=stream.id, name=branch.name, description=branch.description
        )

        assert isinstance(branch.id, str)

    def test_branch_get(self, client, mesh, stream, branch):
        client.commit.create(
            stream_id=stream.id,
            branch_name=branch.name,
            object_id=mesh.id,
            message="a commit for testing branch get",
        )

        fetched_branch = client.branch.get(stream_id=stream.id, name=branch.name)

        assert isinstance(fetched_branch, Branch)
        assert fetched_branch.name == branch.name
        assert fetched_branch.description == branch.description
        assert isinstance(fetched_branch.commits.items, list)
        assert isinstance(fetched_branch.commits.items[0], Commit)

    def test_branch_list(self, client, stream, branch):
        branches = client.branch.list(stream_id=stream.id)
        print(branches)

        assert isinstance(branches, list)
        assert len(branches) == 2
        assert isinstance(branches[0], Branch)
        assert branches[0].name == branch.name

    def test_branch_update(self, client, stream, branch, updated_branch):
        updated = client.branch.update(
            stream_id=stream.id,
            branch_id=branch.id,
            name=updated_branch.name,
            description=updated_branch.description,
        )

        fetched_branch = client.branch.get(
            stream_id=stream.id, name=updated_branch.name
        )

        assert updated is True
        assert fetched_branch.name == updated_branch.name
        assert fetched_branch.description == updated_branch.description

    def test_branch_delete(self, client, stream, branch):
        deleted = client.branch.delete(stream_id=stream.id, branch_id=branch.id)

        assert deleted is True
