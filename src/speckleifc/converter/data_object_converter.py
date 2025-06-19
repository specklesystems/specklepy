from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject

from speckleifc.converter.geometry_converter import geometry_to_speckle


def data_object_to_speckle(
    shape: TriangulationElement | None,
    step_element: entity_instance,
    children: list[Base],
) -> DataObject:
    if shape:
        geometry = cast(Triangulation, shape.geometry)
        display_value = geometry_to_speckle(geometry)
    else:
        display_value = []

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
