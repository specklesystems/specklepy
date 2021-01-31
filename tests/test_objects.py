from speckle.objects.base import Base
from speckle.transports.memory import MemoryTransport
from speckle.api.models import Stream
from speckle.api import operations
from speckle.serialization.base_object_serializer import BaseObjectSerializer
import pytest


class TestObject:
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

    def test_object_create(self, client, stream, base):
        transport = MemoryTransport()
        s = BaseObjectSerializer(write_transports=[transport], read_transport=transport)
        _, base_dict = s.traverse_base(base)
        obj_id = client.object.create(stream_id=stream.id, objects=[base_dict])[0]

        assert isinstance(obj_id, str)
        assert obj_id == base.get_id(True)

    def test_object_get(self, client, stream, base):
        fetched_base = client.object.get(
            stream_id=stream.id, object_id=base.get_id(True)
        )

        assert isinstance(fetched_base, Base)
        assert fetched_base.name == base.name
        assert isinstance(fetched_base.vertices, list)
        assert fetched_base["@detach"]["speckle_type"] == "reference"
