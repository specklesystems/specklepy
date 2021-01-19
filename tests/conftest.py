import uuid
import random
import pytest
import requests
from speckle.api.models import Stream
from speckle.api.client import SpeckleClient
from speckle.objects.base import Base
from speckle.objects.fakemesh import FakeMesh


@pytest.fixture(scope="session")
def host():
    return "127.0.0.1:3000"


@pytest.fixture(scope="session")
def seed_user(host):
    seed = uuid.uuid4().hex
    user_dict = {
        "email": f"{seed[0:7]}@spockle.com",
        "password": "$uper$3cr3tP@ss",
        "name": f"{seed[0:7]} Name",
        "company": "test spockle",
    }

    r = requests.post(
        url=f"http://{host}/auth/local/register?challenge=pyspeckletests",
        data=user_dict,
    )
    access_code = r.url.split("access_code=")[1]

    r_tokens = requests.post(
        url=f"http://{host}/auth/token",
        json={
            "appSecret": "spklwebapp",
            "appId": "spklwebapp",
            "accessCode": access_code,
            "challenge": "pyspeckletests",
        },
    )

    user_dict["token"] = r_tokens.json()["token"]

    return user_dict


@pytest.fixture(scope="session")
def client(host, seed_user):
    client = SpeckleClient(host=host, use_ssl=False)
    client.authenticate(seed_user["token"])
    return client


@pytest.fixture(scope="session")
def sample_stream(client):
    stream = Stream(
        name="a sample stream for testing",
        description="a stream created for testing",
        isPublic=True,
    )
    stream.id = client.stream.create(stream.name, stream.description, stream.isPublic)
    return stream


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