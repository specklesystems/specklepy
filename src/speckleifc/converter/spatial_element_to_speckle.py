from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Triangulation
from specklepy.objects.data_objects import DataObject

from speckleifc.converter.geometry_converter import geometry_to_speckle
from speckleifc.ifc_geometry_processing import get_shape


def spatial_element_to_speckle(step_element: entity_instance) -> DataObject:

    if step_element.Representation is not None:
        shape = get_shape(step_element)
        geometry = cast(Triangulation, shape.geometry)
        display_value = geometry_to_speckle(geometry)
    else:
        display_value = []

    data_object = DataObject(
        applicationId=cast(str, shape.guid),
        properties={},
        name=cast(str, shape.name) or cast(str, shape.guid),
        displayValue=display_value,
    )
    # TODO: children as "elements"
    # data_object["@elements"] = children_converter.convert_children(shape, ifc_model)

    data_object["ifcType"] = step_element.is_a()
    data_object["expressId"] = step_element.id()
    data_object["description"] = cast(str | None, step_element.Description)
    return data_object
