import json
import pytest
from speckle.api import operations
from speckle.transports.server import ServerTransport
from speckle.transports.memory import MemoryTransport
from speckle.serialization.base_object_serializer import BaseObjectSerializer


@pytest.mark.run(order=3)
class TestSerialization:
    def test_serialize(self, base):
        serialized = operations.serialize(base)
        deserialized = operations.deserialize(serialized)

        assert base.get_id() == deserialized.get_id()

    def test_chunking(self, mesh):
        transport = MemoryTransport()
        s = BaseObjectSerializer(write_transports=[transport], read_transport=transport)
        _, serialized = s.write_json(mesh)
        deserialized = s.read_json(serialized)

        serialized_dict = json.loads(serialized)

        assert len(serialized_dict["vertices"]) == 3
        assert len(serialized_dict["@(100)colours"]) == 3
        assert len(serialized_dict["@()default_chunk"]) == 1
        assert serialized_dict["vertices"][0]["speckle_type"] == "reference"
        assert serialized_dict["@(100)colours"][0]["speckle_type"] == "reference"
        assert serialized_dict["@()default_chunk"][0]["speckle_type"] == "reference"
        assert mesh.get_id(True) == deserialized.get_id()

    def test_send_and_receive(self, client, sample_stream, mesh):
        transport = ServerTransport(client=client, stream_id=sample_stream.id)
        hash = operations.send(mesh, transports=[transport])
        received = operations.receive(hash)

        assert mesh.get_id(True) == received.get_id()

        mesh.id = hash  # populate with decomposed id for use in proceeding tests
