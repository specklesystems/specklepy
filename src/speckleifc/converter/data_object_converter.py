from typing import cast

from ifcopenshell.entity_instance import entity_instance
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject


def data_object_to_speckle(
    display_value: list[Base],
    step_element: entity_instance,
    children: list[Base],
) -> DataObject:
    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or guid)

    data_object = DataObject(
        applicationId=guid,
        properties={},
        name=name or guid,
        displayValue=display_value,
    )

    data_object["@elements"] = children
    data_object["ifcType"] = step_element.is_a()
    data_object["expressId"] = step_element.id()
    data_object["description"] = cast(str | None, step_element.Description)
    return data_object
