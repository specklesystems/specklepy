from collections.abc import Generator, Iterable
from typing import cast

from ifcopenshell.entity_instance import entity_instance


def get_aggregates(step_element: entity_instance) -> Generator[entity_instance]:
    for relation in cast(Iterable[entity_instance], step_element.IsDecomposedBy):
        yield from cast(Iterable[entity_instance], relation.RelatedObjects)
