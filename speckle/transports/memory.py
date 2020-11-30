import os
from speckle.logging.exceptions import SpeckleException
from speckle.transports.abstract_transport import AbstractTransport


class MemoryTransport(AbstractTransport):
    _name: str = "Memory"
    objects: dict = {}
    saved_object_count: int = 0

    def __init__(self, name=None) -> None:
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

    def get_object(self, id: str) -> str:
        if id in self.objects:
            return self.objects[id]
        else:
            raise SpeckleException("No object found in this memory transport")

    def begin_write(self) -> None:
        self.saved_object_count = 0

    def end_write(self) -> None:
        pass
