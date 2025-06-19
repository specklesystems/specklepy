from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement
from specklepy.objects.data_objects import DataObject

from speckleifc.converter.geometry_converter import geometry_to_speckle


def data_object_to_speckle(
    shape: TriangulationElement, step_element: entity_instance
) -> DataObject:

    geometry = cast(Triangulation, shape.geometry)
    display_value = geometry_to_speckle(geometry)

    data_object = DataObject(
        applicationId=cast(str, shape.guid),
        properties={},
        name=cast(str, shape.name) or cast(str, shape.guid),
        displayValue=display_value,
    )
    # TODO: children as "elements"
    # data_object["@elements"] = children_converter.convert_children(shape, ifc_model)

    data_object["ifcType"] = cast(str, shape.type)
    data_object["expressId"] = cast(int, shape.id)
    data_object["description"] = cast(str, step_element.Description)
    return data_object
