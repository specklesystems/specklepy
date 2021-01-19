import json
import random

from gql.transport import transport
from speckle.transports.memory import MemoryTransport
from speckle.serialization.base_object_serializer import BaseObjectSerializer
from speckle.api import operations
from speckle.objects.fakemesh import FakeMesh
from speckle.objects.base import Base
import pytest


@pytest.fixture(scope="session")
def mesh():
    mesh = FakeMesh()
    mesh.name = "my_mesh"
    mesh.vertices = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh.faces = [i for i in range(1, 210)]
    mesh["@(100)colours"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh["@()default_chunk"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh.test_bases = [Base(name=i) for i in range(1, 22)]
    mesh["@detach"] = Base(name="detached base")
    return mesh


@pytest.fixture(scope="session")
def base():
    base = Base()
    base.name = "my_base"
    base.vertices = [random.uniform(0, 10) for _ in range(1, 120)]
    base.test_bases = [Base(name=i) for i in range(1, 22)]
    base["@detach"] = Base(name="detached base")
    return base


def test_serialize(base):
    serialized = operations.serialize(base)
    deserialized = operations.deserialize(serialized)

    assert base.get_id() == deserialized.get_id()


def test_chunking(mesh):
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