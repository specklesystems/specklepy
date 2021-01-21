from speckle.api.models import Branch, Commit, Stream
import pytest


class TestBranch:
    @pytest.fixture(scope="module")
    def branch(self):
        return Branch(name="olive branch 🌿", description="a test branch")

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