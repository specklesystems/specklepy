from collections.abc import Generator, Iterable
from itertools import chain
from typing import cast

from ifcopenshell.entity_instance import entity_instance


def get_children(step_element: entity_instance) -> Generator[entity_instance]:
    yield from chain(
        get_spatial_children(step_element), get_aggregate_children(step_element)
    )


def get_spatial_children(step_element: entity_instance) -> Generator[entity_instance]:
    spatial_relations = cast(
        Iterable[entity_instance] | None,
        getattr(step_element, "ContainsElements", None),
    )
    if spatial_relations is not None:
        for relation in spatial_relations:
            yield from cast(Iterable[entity_instance], relation.RelatedElements)


def get_aggregate_children(step_element: entity_instance) -> Generator[entity_instance]:
    aggregate_relations = cast(
        Iterable[entity_instance] | None,
        getattr(step_element, "IsDecomposedBy", None),
    )
    if aggregate_relations is not None:
        for relation in aggregate_relations:
            yield from cast(Iterable[entity_instance], relation.RelatedObjects)
