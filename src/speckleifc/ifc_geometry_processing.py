import multiprocessing

from ifcopenshell import file, ifcopenshell_wrapper, open, sqlite
from ifcopenshell.geom import iterator, settings
from specklepy.logging.exceptions import SpeckleException


def _create_iterator_settings() -> settings:
    ifc_settings = settings()
    # triangles for now, speckle does support n-gons, but may be less performant
    ifc_settings.set("triangulation-type", ifcopenshell_wrapper.TRIANGLE_MESH)
    # no need to weld verts
    ifc_settings.set("weld-vertices", False)
    # Speckle meshes are all in world coords
    ifc_settings.set("use-world-coords", True)
    # Tiny performance improvement,
    ifc_settings.set("no-wire-intersection-check", True)
    # Rendermaterials inherit the material names instead of type + unique id
    ifc_settings.set("use-material-names", True)

    # IfcOpenshell defaults to 0.001mm here, which leads to very dense meshes.
    # lowering the mesh quality a bit here leads to meshes
    # that are still much higher quality than webifc

    # We still need to experiment with the affect on memory usage
    # It may be desirable to lower this further, and increase the angular deflection
    # to compensate. This would allow large meshes to be lower quality,
    # while keeping small meshes relatively similar.
    ifc_settings.set("mesher-linear-deflection", 0.2)

    return ifc_settings


def open_ifc(file_path: str) -> file:
    ifc_file = open(file_path)

    if isinstance(ifc_file, file):
        return ifc_file
    else:
        raise SpeckleException(f"file at {file_path} is not a compatible ifc file type")


def create_geometry_iterator(ifc_file: file | sqlite) -> iterator:
    return iterator(_create_iterator_settings(), ifc_file, multiprocessing.cpu_count())
