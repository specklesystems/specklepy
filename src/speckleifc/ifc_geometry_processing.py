import multiprocessing
from typing import cast

from ifcopenshell import file, ifcopenshell_wrapper, open, sqlite
from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import create_shape, iterator, settings
from ifcopenshell.ifcopenshell_wrapper import TriangulationElement
from specklepy.logging.exceptions import SpeckleException


def _create_base_settings() -> settings:
    ifc_settings = settings()
    ifc_settings.set("triangulation-type", ifcopenshell_wrapper.TRIANGLE_MESH)
    ifc_settings.set("weld-vertices", False)
    ifc_settings.set("use-world-coords", True)

    return ifc_settings


def _create_iterator_settings() -> settings:
    ifc_settings = _create_base_settings()

    return ifc_settings


_IFC_ITERATOR_SETTINGS = _create_iterator_settings()
_IFC_SETTINGS = _create_base_settings()


def open_ifc(file_path: str) -> file:
    ifc_file = open(file_path)

    if isinstance(ifc_file, file):
        return ifc_file
    else:
        raise SpeckleException(f"file at {file_path} is not a compatible ifc file type")


def create_geometry_iterator(ifc_file: file | sqlite) -> iterator:
    return iterator(_IFC_ITERATOR_SETTINGS, ifc_file, multiprocessing.cpu_count() // 2)


def try_get_shape(element: entity_instance) -> TriangulationElement | None:
    representation = getattr(element, "Representation", None)
    if representation is None:
        return None

    has_body = any(
        getattr(r, "RepresentationIdentifier", "").lower() == "body"
        for r in representation.Representations
    )

    if not has_body:
        return None

    shape = create_shape(_IFC_SETTINGS, element)
    return cast(TriangulationElement, shape)
