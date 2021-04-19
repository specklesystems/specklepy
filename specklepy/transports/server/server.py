import requests

from typing import Any, Dict, List, Type

from specklepy.api.client import SpeckleClient
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.abstract_transport import AbstractTransport

from .batch_sender import BatchSender


class ServerTransport(AbstractTransport):
    _name = "RemoteTransport"
    url: str = None
    stream_id: str = None
    saved_obj_count: int = 0
    session: requests.Session = None

    def __init__(self, client: SpeckleClient, stream_id: str, **data: Any) -> None:
        super().__init__(**data)
        # TODO: replace client with account or some other auth avenue
        self.url = client.url
        self.stream_id = stream_id

        token = client.me["token"]
        endpoint = f"{self.url}/objects/{self.stream_id}"
        self._batch_sender = BatchSender(endpoint, token, max_batch_size_mb=1)

        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Accept": "text/plain"}
        )

    def begin_write(self) -> None:
        self.saved_obj_count = 0

    def end_write(self) -> None:
        self._batch_sender.flush()

    def save_object(self, id: str, serialized_object: str) -> None:
        self._batch_sender.send_object(serialized_object)

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        obj_string = source_transport.get_object(id=id)
        self.save_object(id=id, serialized_object=obj_string)

    def get_object(self, id: str) -> str:
        # endpoint = f"{self.url}/objects/{self.stream_id}/{id}/single"
        # r = self.session.get(endpoint, stream=True)

        # _, obj = next(r.iter_lines().decode("utf-8")).split("\t")

        # return obj

        raise SpeckleException(
            "Getting a single object using `ServerTransport.get_object()` is not implemented. To get an object from the server, please use the `SpeckleClient.object.get()` route",
            NotImplementedError,
        )

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        endpoint = f"{self.url}/objects/{self.stream_id}/{id}"
        r = self.session.get(endpoint, stream=True)
        if r.encoding is None:
            r.encoding = "utf-8"
        lines = r.iter_lines(decode_unicode=True)

        # save first (root) obj for return
        root_hash, root_obj = next(lines).split("\t")
        target_transport.save_object(root_hash, root_obj)

        # iter through returned objects saving them as we go
        for line in lines:
            if line:
                hash, obj = line.split("\t")
                target_transport.save_object(hash, obj)

        return root_obj

    # async def stream_res(self, endpoint: str) -> str:
    #     data = b""
    #     async with aiohttp.ClientSession() as session:
    #         session.headers.update(
    #             {
    #                 "Authorization": f"{self.session.headers['Authorization']}",
    #                 "Accept": "text/plain",
    #             }
    #         )
    #         async with session.get(endpoint) as res:
    #             while True:
    #                 chunk = await res.content.read(self.chunk_size)
    #                 if not chunk:
    #                     break
    #                 data += chunk

    #     return data.decode("utf-8")
