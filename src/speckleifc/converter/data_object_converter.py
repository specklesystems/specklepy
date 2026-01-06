from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_parent

from speckleifc.property_extraction import extract_properties
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject


def data_object_to_speckle(
    display_value: list[Base],
    step_element: entity_instance,
    children: list[Base],
    current_storey: str | None = None,
) -> DataObject:
    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or guid)

    properties = extract_properties(step_element)

    # Add parent ID only if element's parent is also a DataObject (not a Collection)
    parent_element = get_parent(step_element)
    if parent_element and hasattr(parent_element, 'GlobalId'):
        # Collections are: IfcProject and IfcSpatialStructureElement types
        if not parent_element.is_a("IfcProject") and not parent_element.is_a("IfcSpatialStructureElement"):
            properties["parentApplicationId"] = parent_element.GlobalId

    # Add building storey information if available and not a building storey itself
    if current_storey and not step_element.is_a("IfcBuildingStorey"):
        properties["Building Storey"] = current_storey

    data_object = DataObject(
        applicationId=guid,
        properties=properties,
        name=name or guid,
        displayValue=display_value,
    )

    data_object["@elements"] = children
    data_object["ifcType"] = step_element.is_a()

    return data_object
