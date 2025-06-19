from collections.abc import Sequence
from typing import cast

from attrs import define
from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Element
from ifcopenshell.util.element import get_container
from specklepy.objects.base import Base
from specklepy.objects.graph_traversal.commit_object_builder import (
    get_detached_prop,
    set_detached_prop,
)

ROOT: int = -1
ELEMENTS = "elements"

PARENT_INFO = tuple[int | None, str]


@define(slots=True)
class RootObjectBuilder:
    converted: dict[int, Base]
    _parent_infos: dict[int, Sequence[PARENT_INFO]]

    def __init__(self) -> None:
        self.converted = {}
        self._parent_infos = {}

    def include_object(
        self,
        conversion_result: Base,
        step_element: entity_instance,
        shape: Element | None,
    ) -> None:
        step_id = step_element.id()
        self.converted[step_id] = conversion_result

        if shape is None:
            parent = get_container(step_element)
            parent_id = parent.id() if parent else None
        else:
            parent_id = cast(int, shape.parent_id)

        self.set_relationship(step_id, ((parent_id, ELEMENTS), (ROOT, ELEMENTS)))

    def build_commit_object(self, root_commit_object: Base) -> None:
        self.apply_relationships(root_commit_object)

    def set_relationship(
        self, step_id: int, parent_info: Sequence[PARENT_INFO]
    ) -> None:
        self._parent_infos[step_id] = parent_info

    def apply_relationships(self, root_commit_object: Base) -> None:
        for step_id, c in self.converted.items():

            if step_id not in self._parent_infos:
                continue

            try:
                self.apply_relationship(c, step_id, root_commit_object)
            except Exception as ex:
                print(f"Failed to add object {type(c)} to commit object: {ex}")

    def apply_relationship(
        self, current: Base, step_id: int, root_commit_object: Base
    ) -> None:
        parents = self._parent_infos[step_id]

        for parent_id, prop_name in parents:
            if not parent_id:
                continue

            parent: Base | None
            if parent_id == ROOT:
                parent = root_commit_object
            else:
                parent = self.converted.get(parent_id, None)

            if not parent:
                continue

            elements = get_detached_prop(parent, prop_name)
            if not isinstance(elements, list):
                elements = []
                set_detached_prop(parent, prop_name, elements)

            elements.append(current)
            return

        raise Exception(
            f"Could not find a valid parent for object of type {type(current)}."
            f"Checked {len(parents)} potential parent, and non were converted!"
        )
