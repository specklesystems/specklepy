import uuid
import pytest
import requests
from speckle.api.client import SpeckleClient


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
