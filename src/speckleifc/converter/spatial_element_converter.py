from typing import cast

from ifcopenshell.entity_instance import entity_instance
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject
from specklepy.objects.models.collections.collection import Collection

from speckleifc.property_extraction import extract_properties


def spatial_element_to_speckle(
    display_value: list[Base],
    step_element: entity_instance,
    relational_children: list[Base],
) -> Collection:
    direct_geometry = _convert_as_data_object(display_value, step_element)
    all_children = [direct_geometry] + relational_children

    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or step_element.LongName or guid)

    data_object = Collection(applicationId=guid, name=name, elements=all_children)
    data_object["ifcType"] = step_element.is_a()

    return data_object


def _convert_as_data_object(
    display_value: list[Base], step_element: entity_instance
) -> DataObject:
    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or step_element.LongName or guid)
    data_object = DataObject(
        applicationId=guid,
        properties=extract_properties(step_element),
        name=name,
        displayValue=display_value,
    )

    data_object["ifcType"] = step_element.is_a()

    return data_object
