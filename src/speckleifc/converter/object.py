"""Object conversion (the ``objects``/eav namespace): turn one IFC element into its
object row — properties, name, ifcType — plus its geometry placements."""

from __future__ import annotations

from typing import cast

from ifcopenshell.entity_instance import entity_instance

from speckleifc.property_extraction import extract_properties
from specklepy.bundle.builder import BundleBuilder, BundleDefinition, BundleObject

DATA_OBJECT_SPECKLE_TYPE = "Objects.Data.DataObject"

Placement = tuple[list[float], list[BundleDefinition]]
"""(row-major transform, one definition per non-empty style mesh)"""


def convert_object(
    builder: BundleBuilder,
    element: entity_instance,
    name: str,
    *,
    storey_name: str | None = None,
    placement: Placement | None = None,
) -> BundleObject:
    guid = cast(str, element.GlobalId)
    obj = builder.get_or_add_object(guid)

    properties = extract_properties(element)
    if storey_name and not element.is_a("IfcBuildingStorey"):
        properties["Building Storey"] = storey_name
    parent = _product_parent_of(element)
    if parent is not None:
        properties["parentApplicationId"] = parent.GlobalId

    obj.set_properties(
        properties,
        name=name,
        speckle_type=DATA_OBJECT_SPECKLE_TYPE,
        root_scalars=[("ifcType", element.is_a())],
    )

    if placement is not None:
        transform, definitions = placement
        for definition in definitions:
            obj.place(definition, transform, "m", key=f"{guid}:{definition.key}")
    return obj


def _product_parent_of(element: entity_instance) -> entity_instance | None:
    for rel in getattr(element, "Decomposes", None) or []:
        parent = rel.RelatingObject
        if (
            parent is not None
            and hasattr(parent, "GlobalId")
            and not parent.is_a("IfcProject")
            and not parent.is_a("IfcSpatialStructureElement")
        ):
            return parent
    return None
