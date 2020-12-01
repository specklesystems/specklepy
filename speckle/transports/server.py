import json
from speckle.logging.exceptions import SpeckleException
import requests
from asyncio import Queue, Task
from speckle.api.client import SpeckleClient
from typing import Dict, List
from speckle.transports.abstract_transport import AbstractTransport


class ServerTransport(AbstractTransport):
    _name = "RemoteTransport"
    url: str = None
    stream_id: str = None
    saved_obj_count: int = 0
    session: requests.Session = None
    __queue: Queue = None
    __workers: List[Task] = []

    def __init__(self, client: SpeckleClient, stream_id: str) -> None:
        # TODO: replace client with account or some other auth avenue
        self.url = client.url
        self.stream_id = stream_id
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {client.me['token']}"})

    def begin_write(self) -> None:
        self.saved_obj_count = 0

    def end_write(self) -> None:
        pass

    # TODO: add save task to queue and process as the root is being deserialised
    def save_object(self, id: str, serialized_object: str) -> None:
        endpoint = f"{self.url}/objects/{self.stream_id}"
        r = self.session.post(
            url=endpoint,
            files={"batch-1": ("batch-1", f"[{serialized_object}]")},
        )
        if r.status_code != 201:
            raise SpeckleException(
                message=f"Could not save the object to the server - status code {r.status_code}"
            )

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        pass

    def get_object(self, id: str) -> str:
        endpoint = f"{self.url}/objects/{self.stream_id}/{id}/single"
        r = self.session.get(url=endpoint)
        print(r.text)

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        raise NotImplementedError
