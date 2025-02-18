import random
import uuid
from typing import Dict
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from specklepy.api.client import SpeckleClient
from specklepy.core.api import operations
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models import Version
from specklepy.core.api.models.current import Project
from specklepy.logging import metrics
from specklepy.objects.base import Base
from specklepy.objects.geometry import Point
from specklepy.transports.server.server import ServerTransport

from .fakemesh import FakeDirection, FakeMesh

metrics.disable()


@pytest.fixture(scope="session")
def host() -> str:
    return "localhost:3000"


def seed_user(host: str) -> Dict[str, str]:
    seed = uuid.uuid4().hex
    user_dict = {
        "email": f"{seed[0:7]}@example.org",
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
    redirect_url = urlparse(r.headers.get("location"))
    access_code = parse_qs(redirect_url.query)["access_code"][0]  # type: ignore

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


def create_version(client: SpeckleClient, project_id: str, model_id: str) -> Version:
    remote = ServerTransport(project_id, client)
    objectId = operations.send(
        Base(applicationId="ASDF"), [remote], use_default_cache=False
    )
    input = CreateVersionInput(
        object_id=objectId, model_id=model_id, project_id=project_id
    )
    return client.version.create(input)


@pytest.fixture(scope="session")
def user_dict(host: str) -> Dict[str, str]:
    return seed_user(host)


@pytest.fixture(scope="session")
def second_user_dict(host: str) -> Dict[str, str]:
    return seed_user(host)


def create_client(host: str, token: str) -> SpeckleClient:
    client = SpeckleClient(host=host, use_ssl=False)
    client.authenticate_with_token(token)
    user = client.active_user.get()
    assert user
    client.account.userInfo.id = user.id
    client.account.userInfo.email = user.email
    client.account.userInfo.name = user.name
    client.account.userInfo.company = user.company
    client.account.userInfo.avatar = user.avatar
    return client


@pytest.fixture(scope="session")
def client(host: str, user_dict: Dict[str, str]) -> SpeckleClient:
    return create_client(host, user_dict["token"])


@pytest.fixture(scope="session")
def second_client(host: str, second_user_dict: Dict[str, str]):
    return create_client(host, second_user_dict["token"])


@pytest.fixture(scope="session")
def sample_project(client: SpeckleClient) -> Project:
    input = ProjectCreateInput(
        name="a sample stream for testing",
        description="a stream created for testing",
        visibility=ProjectVisibility.PUBLIC,
    )
    return client.project.create(input)


@pytest.fixture(scope="session")
def mesh() -> FakeMesh:
    mesh = FakeMesh()
    mesh.name = "my_mesh"
    mesh.vertices = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh.faces = list(range(1, 210))
    mesh["@(100)colours"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh["@()default_chunk"] = [random.uniform(0, 10) for _ in range(1, 210)]
    mesh.cardinal_dir = FakeDirection.WEST
    mesh.test_bases = [Base(applicationId=f"test {i}") for i in range(1, 22)]
    mesh.detach_this = Base(applicationId="predefined detached base")
    mesh["@detach"] = Base(applicationId="detached base")
    mesh["@detached_list"] = [
        42,
        "some text",
        [1, 2, 3],
        Base(applicationId="detached within a list"),
    ]
    mesh.origin = Point(x=4, y=2, z=0, units="m")
    return mesh
