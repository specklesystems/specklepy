import json

import pytest

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.core.api.models.current import Project
from specklepy.objects.base import Base
from specklepy.objects.geometry import Point
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport

from .fakemesh import FakeMesh


@pytest.mark.run(order=5)
class TestSerialization:
    def test_serialize(self, base: Base):
        serialized = operations.serialize(base)
        deserialized = operations.deserialize(serialized)

        assert base.get_id() == deserialized.get_id()
        assert base.units == "millimetres"
        assert isinstance(base.test_bases[0], Base)
        assert base["@revit_thing"].speckle_type == "SpecialRevitFamily"
        assert base["@detach"].applicationId == deserialized["@detach"].applicationId

    def test_detaching(self, mesh: FakeMesh):
        transport = MemoryTransport()
        serialized = operations.serialize(mesh, [transport])
        deserialized = operations.deserialize(serialized, transport)

        serialized_dict = json.loads(serialized)

        assert serialized_dict["detach_this"]["speckle_type"] == "reference"
        assert serialized_dict["@detach"]["speckle_type"] == "reference"
        assert serialized_dict["origin"]["speckle_type"] == "reference"
        assert serialized_dict["@detached_list"][-1]["speckle_type"] == "reference"
        assert mesh.get_id() == deserialized.get_id()

    def test_chunking(self, mesh: FakeMesh):
        transport = MemoryTransport()
        serialized = operations.serialize(mesh, [transport])
        deserialized = operations.deserialize(serialized, transport)

        serialized_dict = json.loads(serialized)

        assert len(serialized_dict["vertices"]) == 3
        assert len(serialized_dict["@(100)colours"]) == 3
        assert len(serialized_dict["@()default_chunk"]) == 1
        assert serialized_dict["vertices"][0]["speckle_type"] == "reference"
        assert serialized_dict["@(100)colours"][0]["speckle_type"] == "reference"
        assert serialized_dict["@()default_chunk"][0]["speckle_type"] == "reference"
        assert mesh.get_id() == deserialized.get_id()

    def test_send_and_receive(
        self, client: SpeckleClient, sample_project: Project, mesh: FakeMesh
    ):
        transport = ServerTransport(client=client, stream_id=sample_project.id)
        hash = operations.send(mesh, transports=[transport])

        # also try constructing server transport with token and url
        transport = ServerTransport(
            stream_id=sample_project.id, token=client.account.token, url=client.url
        )
        # use a fresh memory transport to force receiving from remote
        received = operations.receive(
            hash, remote_transport=transport, local_transport=MemoryTransport()
        )

        assert isinstance(received, FakeMesh)
        assert received.vertices == mesh.vertices
        assert isinstance(received.origin, Point)
        assert received.origin.x == mesh.origin.x
        # not comparing hashes as order is not guaranteed back from server

        mesh.id = hash  # populate with decomposed id for use in proceeding tests

    def test_receive_local(self, client: SpeckleClient, mesh: FakeMesh):
        hash = operations.send(mesh)  # defaults to SQLiteTransport
        received = operations.receive(hash)

        assert isinstance(received, Base)
        assert mesh.get_id() == received.get_id()

    def test_unknown_type(self):
        unknown = '{"speckle_type": "mysterious.type"}'
        deserialised = operations.deserialize(unknown)

        assert isinstance(deserialised, Base)
        assert deserialised.speckle_type == "mysterious.type"

    def test_no_speckle_type(self):
        untyped = '{"foo": "bar"}'
        deserialised = operations.deserialize(untyped)

        assert deserialised == {"foo": "bar"}

    def test_big_int(self):
        big_int = '{"big": ' + str(2**64) + "}"
        deserialised = operations.deserialize(big_int)

        assert deserialised == {"big": 2**64}
