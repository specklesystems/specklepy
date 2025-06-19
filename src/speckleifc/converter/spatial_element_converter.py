from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement
from specklepy.objects.data_objects import DataObject

from speckleifc.converter.geometry_converter import geometry_to_speckle


def spatial_element_to_speckle(
    step_element: entity_instance, shape: TriangulationElement | None
) -> DataObject:

    if shape is not None:
        geometry = cast(Triangulation, shape.geometry)
        display_value = geometry_to_speckle(geometry)
    else:
        display_value = []

    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or step_element.LongName or guid)
    data_object = DataObject(
        applicationId=guid,
        properties={},
        name=name,
        displayValue=display_value,
    )
    # TODO: children as "elements"
    # data_object["@elements"] = children_converter.convert_children(shape, ifc_model)

    data_object["expressId"] = step_element.id()
    data_object["ifcType"] = step_element.is_a()
    data_object["description"] = cast(str | None, step_element.Description)
    data_object["objectType"] = step_element.ObjectType
    data_object["compositionType"] = step_element.CompositionType
    data_object["longName"] = step_element.LongName

    return data_object
