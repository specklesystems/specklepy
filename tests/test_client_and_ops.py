import pytest
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.objects.base import Base
from specklepy.transports.server import ServerTransport
from specklepy.logging.exceptions import SpeckleException


def test_invalid_authentication():
    client = SpeckleClient()

    with pytest.raises(SpeckleException):
        client.authenticate("fake token")


def test_invalid_send():
    client = SpeckleClient()
    client.me = {"token": "fake token"}
    transport = ServerTransport("3073b96e86", client)

    with pytest.raises(SpeckleException):
        operations.send(Base(), [transport])


def test_invalid_receive():
    client = SpeckleClient()
    client.me = {"token": "fake token"}
    transport = ServerTransport("fake stream", client)

    with pytest.raises(SpeckleException):
        operations.receive("fake object", transport)
