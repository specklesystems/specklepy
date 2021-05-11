import json
from typing import Any, List, Dict
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.abstract_transport import AbstractTransport


class MemoryTransport(AbstractTransport):
    _name: str = "Memory"
    objects: dict = {}
    saved_object_count: int = 0

    def __init__(self, name=None, **data: Any) -> None:
        super().__init__(**data)
        if name:
            self._name = name

    def __repr__(self) -> str:
        return f"MemoryTransport(objects: {len(self.objects)})"

    def save_object(self, id: str, serialized_object: str) -> None:
        self.objects[id] = serialized_object

        self.saved_object_count += 1

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        raise NotImplementedError

    def get_object(self, id: str) -> str or None:
        if id in self.objects:
            return self.objects[id]
        else:
            return None

    def has_objects(self, id_list: List[str]) -> Dict[str, bool]:
        return {id: (id in self.objects) for id in id_list}

    def begin_write(self) -> None:
        self.saved_object_count = 0

    def end_write(self) -> None:
        pass

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        raise NotImplementedError
