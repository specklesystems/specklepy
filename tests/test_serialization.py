import json
import pytest
from speckle.api import operations
from speckle.transports.server import ServerTransport
from speckle.transports.memory import MemoryTransport
from speckle.serialization.base_object_serializer import BaseObjectSerializer
from speckle.objects.base import Base
from speckle.objects.point import Point
from speckle.objects.fakemesh import FakeMesh


@pytest.mark.run(order=3)
class TestSerialization:
    def test_serialize(self, base):
        serialized = operations.serialize(base)
        deserialized = operations.deserialize(serialized)

        assert base.get_id() == deserialized.get_id()
        assert base.units == "mm"
        assert isinstance(base.test_bases[0], Base)
        assert base["@detach"].name == deserialized["@detach"].name

    def test_detaching(self, mesh):
        transport = MemoryTransport()
        s = BaseObjectSerializer(write_transports=[transport], read_transport=transport)
        _, serialized = s.write_json(mesh)
        deserialized = s.read_json(serialized)

        serialized_dict = json.loads(serialized)

        assert serialized_dict["detach_this"]["speckle_type"] == "reference"
        assert serialized_dict["@detach"]["speckle_type"] == "reference"
        assert serialized_dict["origin"]["speckle_type"] == "reference"
        assert mesh.get_id(True) == deserialized.get_id()

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
        # use a fresh memory transport to force receiving from remote
        received = operations.receive(
            hash, remote_transport=transport, local_transport=MemoryTransport()
        )

        assert isinstance(received, FakeMesh)
        assert received.vertices == mesh.vertices
        assert isinstance(received.origin, Point)
        assert received.origin.value == mesh.origin.value
        assert mesh.get_id(True) == received.get_id()

        mesh.id = hash  # populate with decomposed id for use in proceeding tests

    def test_receive_local(self, client, mesh):
        received = operations.receive(mesh.id)  # defaults to SQLiteTransport

        assert isinstance(received, Base)
        assert mesh.get_id(True) == received.get_id()

    def test_unknown_type(self):
        unknown = '{"speckle_type": "mysterious.type"}'
        deserialised = operations.deserialize(unknown)

        assert isinstance(deserialised, Base)
        assert deserialised.speckle_type == "mysterious.type"
