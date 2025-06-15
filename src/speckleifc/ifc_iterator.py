import multiprocessing

from ifcopenshell import file, ifcopenshell_wrapper, open, sqlite
from ifcopenshell.geom import iterator, settings
from specklepy.logging.exceptions import SpeckleException


def _create_settings() -> settings:
    ifc_settings = settings()
    ifc_settings.set("triangulation-type", ifcopenshell_wrapper.TRIANGLE_MESH)
    ifc_settings.set("weld-vertices", False)
    ifc_settings.set("use-world-coords", True)
    ifc_settings.set("use-world-coords", True)

    return ifc_settings


def open_ifc(file_path: str) -> file:
    ifc_file = open(file_path)

    if isinstance(ifc_file, file):
        return ifc_file
    else:
        raise SpeckleException(f"file at {file_path} is not a compatible ifc file type")


def create_geometry_iterator(ifc_file: file | sqlite) -> iterator:
    settings = _create_settings()

    return iterator(settings, ifc_file, multiprocessing.cpu_count())
