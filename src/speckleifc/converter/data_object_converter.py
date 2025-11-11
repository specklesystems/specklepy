from typing import cast

from ifcopenshell.entity_instance import entity_instance

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
