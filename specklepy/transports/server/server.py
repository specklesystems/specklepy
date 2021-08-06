import json
import time

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
        if not client.me:
            raise SpeckleException("The provided SpeckleClient was not authenticated.")
        self.url = client.url
        self.stream_id = stream_id

        token = client.me["token"]
        self._batch_sender = BatchSender(
            self.url, self.stream_id, token, max_batch_size_mb=1
        )

        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Accept": "text/plain"}
        )

    def begin_write(self) -> None:
        self.saved_obj_count = 0

    def end_write(self) -> None:
        self._batch_sender.flush()

    def save_object(self, id: str, serialized_object: str) -> None:
        self._batch_sender.send_object(id, serialized_object)

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

    def has_objects(self, id_list: List[str]) -> Dict[str, bool]:
        return {id: False for id in id_list}

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        endpoint = f"{self.url}/objects/{self.stream_id}/{id}/single"
        r = self.session.get(endpoint)
        if r.encoding is None:
            r.encoding = "utf-8"

        if r.status_code != 200:
            raise SpeckleException(
                f"Can't get object {self.stream_id}/{id}: HTTP error {r.status_code} ({r.text[:1000]})"
            )
        root_obj_serialized = r.text
        root_obj = json.loads(root_obj_serialized)
        closures = root_obj.get("__closure", {})

        # Check which children are not already in the target transport
        children_ids = list(closures.keys())
        children_found_map = target_transport.has_objects(children_ids)
        new_children_ids = [
            id for id in children_found_map if not children_found_map[id]
        ]

        # Get the new children
        endpoint = f"{self.url}/api/getobjects/{self.stream_id}"
        r = self.session.post(
            endpoint, data={"objects": json.dumps(new_children_ids)}, stream=True
        )
        if r.encoding is None:
            r.encoding = "utf-8"
        lines = r.iter_lines(decode_unicode=True)

        # iter through returned objects saving them as we go
        for line in lines:
            if line:
                hash, obj = line.split("\t")
                target_transport.save_object(hash, obj)

        target_transport.save_object(id, root_obj_serialized)

        return root_obj_serialized

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
