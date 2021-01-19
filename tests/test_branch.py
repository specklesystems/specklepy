from speckle.api.models import Branch, Stream
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
