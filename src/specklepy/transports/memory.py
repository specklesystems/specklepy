from typing import Dict, List

from specklepy.transports.abstract_transport import AbstractTransport


class MemoryTransport(AbstractTransport):
    def __init__(self, name="Memory") -> None:
        super().__init__()
        self._name = name
        self.objects = {}
        self.saved_object_count = 0

    @property
    def name(self) -> str:
        return self._name

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
        return self.objects[id] if id in self.objects else None

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
