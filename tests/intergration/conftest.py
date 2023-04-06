import random
import uuid

import pytest
import requests

from specklepy.api.client import SpeckleClient
from specklepy.api.models import Stream
from specklepy.logging import metrics
from specklepy.objects.base import Base
from specklepy.objects.fakemesh import FakeDirection, FakeMesh
from specklepy.objects.geometry import Point
from urllib.parse import urlparse, parse_qs


metrics.disable()


@pytest.fixture(scope="session")
def host():
    return "localhost:3000"


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
        # do not follow redirects here, they lead to the frontend, which might not be
        # running in a test environment
        # causing the response to not be OK in the end
        allow_redirects=False,
    )
    if not r.ok:
        raise Exception(f"Cannot seed user: {r.reason}")
    redirect_url = urlparse(r.headers.get('location'))
    access_code = parse_qs(redirect_url.query)['access_code'][0] # type: ignore

    r_tokens = requests.post(
        url=f"http://{host}/auth/token",
        json={
            "appSecret": "spklwebapp",
            "appId": "spklwebapp",
            "accessCode": access_code,
            "challenge": "pyspeckletests",
        },
    )

    user_dict.update(**r_tokens.json())

    return user_dict


@pytest.fixture(scope="session")
def user_dict(host):
    return seed_user(host)


@pytest.fixture(scope="session")
def second_user_dict(host):
    return seed_user(host)


@pytest.fixture(scope="session")
def client(host, user_dict):
    client = SpeckleClient(host=host, use_ssl=False)
    client.authenticate_with_token(user_dict["token"])
    return client


@pytest.fixture(scope="session")
def second_client(host, second_user_dict):
    client = SpeckleClient(host=host, use_ssl=False)
    client.authenticate_with_token(second_user_dict["token"])
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
    mesh.faces = list(range(1, 210))
    mesh["@(100)colours"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh["@()default_chunk"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh.cardinal_dir = FakeDirection.WEST
    mesh.test_bases = [Base(name=f"test {i}") for i in range(1, 22)]
    mesh.detach_this = Base(name="predefined detached base")
    mesh["@detach"] = Base(name="detached base")
    mesh["@detached_list"] = [
        42,
        "some text",
        [1, 2, 3],
        Base(name="detached within a list"),
    ]
    mesh.origin = Point(x=4, y=2)
    return mesh
