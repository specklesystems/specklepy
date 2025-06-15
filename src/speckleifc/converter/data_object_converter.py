from typing import cast

from ifcopenshell import file
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement
from specklepy.objects.data_objects import DataObject

from speckleifc.converter.geometry_converter import geometry_to_speckle


def data_object_to_speckle(shape: TriangulationElement, ifc_model: file) -> DataObject:

    geometry = cast(Triangulation, shape.geometry)
    display_value = geometry_to_speckle(geometry, ifc_model)

    data_object = DataObject(
        applicationId=cast(str, shape.guid),
        properties={},
        name=cast(str, shape.name) or cast(str, shape.guid),
        displayValue=display_value,
    )
    # TODO: children as "elements"
    # data_object["@elements"] = children_converter.convert_children(shape, ifc_model)

    data_object["ifcType"] = cast(str, shape.type)
    data_object["expressId"] = cast(str, shape.id)
    data_object["ownerId"] = cast(str, shape.parent_id)
    data_object["description"] = cast(str, shape.unique_id)
    return data_object
