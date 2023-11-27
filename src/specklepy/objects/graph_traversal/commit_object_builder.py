from abc import ABC, abstractmethod
from typing import Any, Collection, Dict, Generic, Iterable, Optional, Tuple, TypeVar

from attrs import define

from specklepy.objects.base import Base

ROOT: str = "__Root"

T = TypeVar("T")
PARENT_INFO = Tuple[Optional[str], str]


@define(slots=True)
class CommitObjectBuilder(ABC, Generic[T]):
    converted: Dict[str, Base]
    _parent_infos: Dict[str, Collection[PARENT_INFO]]

    def __init__(self) -> None:
        self.converted = {}
        self._parent_infos = {}

    @abstractmethod
    def include_object(self, conversion_result: Base, native_object: T) -> None:
        pass

    def build_commit_object(self, root_commit_object: Base) -> None:
        self.apply_relationships(self.converted.values(), root_commit_object)

    def set_relationship(
        self, app_id: Optional[str], *parent_info: PARENT_INFO
    ) -> None:
        if not app_id:
            return

        self._parent_infos[app_id] = parent_info

    def apply_relationships(
        self, to_add: Iterable[Base], root_commit_object: Base
    ) -> None:
        for c in to_add:
            try:
                self.apply_relationship(c, root_commit_object)
            except Exception as ex:
                print(f"Failed to add object {type(c)} to commit object: {ex}")

    def apply_relationship(self, current: Base, root_commit_object: Base):
        if not current.applicationId:
            raise Exception("Expected applicationId to have been set")

        parents = self._parent_infos[current.applicationId]

        for parent_id, prop_name in parents:
            if not parent_id:
                continue

            parent: Optional[Base]
            if parent_id == ROOT:
                parent = root_commit_object
            else:
                parent = (
                    self.converted[parent_id] if parent_id in self.converted else None
                )

            if not parent:
                continue

            try:
                elements = get_detached_prop(parent, prop_name)
                if not isinstance(elements, list):
                    elements = []
                    set_detached_prop(parent, prop_name, elements)

                elements.append(current)
                return
            except Exception as ex:
                # A parent was found, but it was invalid (Likely because of a type mismatch on a `elements` property)
                print(
                    f"Failed to add object {type(current)} to a converted parent; {ex}"
                )

            raise Exception(
                f"Could not find a valid parent for object of type {type(current)}. Checked {len(parents)} potential parent, and non were converted!"
            )


def get_detached_prop(speckle_object: Base, prop_name: str) -> Optional[Any]:
    detached_prop_name = get_detached_prop_name(speckle_object, prop_name)
    return getattr(speckle_object, detached_prop_name, None)


def set_detached_prop(
    speckle_object: Base, prop_name: str, value: Optional[Any]
) -> None:
    detached_prop_name = get_detached_prop_name(speckle_object, prop_name)
    setattr(speckle_object, detached_prop_name, value)


def get_detached_prop_name(speckle_object: Base, prop_name: str) -> str:
    return prop_name if hasattr(speckle_object, prop_name) else f"@{prop_name}"
