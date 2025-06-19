from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject
from specklepy.objects.models.collections.collection import Collection

from speckleifc.converter.geometry_converter import geometry_to_speckle


def spatial_element_to_speckle(
    shape: TriangulationElement | None,
    step_element: entity_instance,
    relational_children: list[Base],
) -> Collection:

    direct_geometry = _convert_as_data_object(shape, step_element)
    all_children = [direct_geometry] + relational_children

    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or step_element.LongName or guid)

    data_object = Collection(applicationId=guid, name=name, elements=all_children)
    data_object["expressId"] = step_element.id()
    data_object["ifcType"] = step_element.is_a()

    return data_object


def _convert_as_data_object(
    shape: TriangulationElement | None, step_element: entity_instance
) -> DataObject:

    # Some types of SpatialElements, like IfcSite have a geometry representation
    # Using get_shape is not as efficient as the using the geometry iterator,
    # like is used for most of the geometry conversion, but for a few IfcSites is fine.
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

    data_object["expressId"] = step_element.id()
    data_object["ifcType"] = step_element.is_a()
    data_object["description"] = cast(str | None, step_element.Description)
    data_object["objectType"] = step_element.ObjectType
    data_object["compositionType"] = step_element.CompositionType
    data_object["longName"] = step_element.LongName

    return data_object
