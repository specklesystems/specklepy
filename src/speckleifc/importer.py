from specklepy.logging.exceptions import SpeckleException  # noqa: I001
from ifcopenshell import file
from ifcopenshell.ifcopenshell_wrapper import TriangulationElement
from speckleifc.converter.data_object_converter import data_object_to_speckle
from speckleifc.ifc_iterator import create_geometry_iterator, open_ifc
from specklepy.objects import Base
from specklepy.objects.models.collections.collection import Collection


def convert_file(file_path: str) -> Collection:
    file = open_ifc(file_path)
    iterator = create_geometry_iterator(file)

    if not iterator.initialize():
        raise SpeckleException("Iterator failed to initialize")

    converted_geometry: list[Base] = []

    while True:
        element = iterator.get()
        assert isinstance(element, TriangulationElement)

        converted = convert_geometry_element(element, file)
        converted_geometry.append(converted)

        if not iterator.next():
            break

    return Collection(name="root collection", elements=converted_geometry)


def convert_geometry_element(
    geometry_element: TriangulationElement, ifc_model: file
) -> Base:
    # step_entity = ifc_model.by_id(geometry_element.id())
    return data_object_to_speckle(geometry_element, ifc_model)
