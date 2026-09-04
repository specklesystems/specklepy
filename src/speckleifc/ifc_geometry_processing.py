import multiprocessing

from ifcopenshell import SchemaError, file, ifcopenshell_wrapper, open, sqlite
from ifcopenshell.geom import iterator, settings

from specklepy.logging.exceptions import SpeckleException


def _create_iterator_settings() -> settings:
    ifc_settings = settings()
    # triangles for now, speckle does support n-gons, but may be less performant
    ifc_settings.set("triangulation-type", ifcopenshell_wrapper.TRIANGLE_MESH)
    # no need to weld verts
    ifc_settings.set("weld-vertices", False)
    #
    ifc_settings.set("use-world-coords", False)
    ifc_settings.set("permissive-shape-reuse", True)

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
    try:
        ifc_file = open(file_path)
    except SchemaError:
        raise
    except FileNotFoundError:
        raise
    except Exception as ex:
        raise SpeckleException("File could not be opened as an IFC file") from ex

    if isinstance(ifc_file, file):
        return ifc_file
    else:
        raise SpeckleException(f"file at {file_path} is not a compatible ifc file type")


# RepresentationType values that carry 3D shape (IFC2x3 + IFC4 vocabularies).
# Curve-only types (Curve2D, GeometricCurveSet, Annotation2D, ...) are deliberately
# absent: they never yield a solid and must not steer context selection.
_3D_REPRESENTATION_TYPES = frozenset(
    t.lower()
    for t in (
        "SweptSolid",
        "AdvancedSweptSolid",
        "Brep",
        "AdvancedBrep",
        "CSG",
        "Clipping",
        "SurfaceModel",
        "SolidModel",
        "Tessellation",
        "MappedRepresentation",
        "SectionedSpine",
    )
)

# What IfcOpenShell's own default picks (mapping.cpp,
# addRepresentationsFromDefaultContexts): top-level contexts of these types, plus
# their sub-contexts.
_DEFAULT_CONTEXT_TYPES = frozenset(("model", "design", "model view", "detail view"))


def contexts_for_3d_representations(ifc_file: file) -> list[int]:
    """Context ids IfcOpenShell should read: its own default choice, widened with every
    context a 3D shape representation actually points at.

    IfcOpenShell selects representations context-first. With the default settings it
    keeps the Model-family contexts (+ sub-contexts) and only falls back to "all
    contexts" when those hold *nothing*. Some exporters (ICPrefab/iTConcrete precast
    files, ENG-9524) attach every Body representation to a *Plan* context; one stray
    FootPrint curve in a Model sub-context then defeats the fallback and the whole file
    reads as empty. Building the id set from the representations themselves makes the
    selection evidence-based while staying a strict superset of the default, so nothing
    the default converts is lost.
    """
    ids: set[int] = set()
    for context in ifc_file.by_type("IfcGeometricRepresentationContext", False):
        context_type = (context.ContextType or "").lower()
        if context_type in _DEFAULT_CONTEXT_TYPES:
            ids.add(context.id())
            for sub in context.HasSubContexts or ():
                ids.add(sub.id())
    for rep in ifc_file.by_type("IfcShapeRepresentation"):
        is_3d = (rep.RepresentationType or "").lower() in _3D_REPRESENTATION_TYPES
        if is_3d and rep.ContextOfItems is not None:
            ids.add(rep.ContextOfItems.id())
    return sorted(ids)


def create_geometry_iterator(
    ifc_file: file | sqlite, context_ids: list[int] | None = None
) -> iterator:
    GEOMETRY_LIBRARY = "hybrid-opencascade-cgal"  # First OCC then fallback to CGAL
    ifc_settings = _create_iterator_settings()
    if context_ids:
        ifc_settings.set("context-ids", context_ids)
    return iterator(
        ifc_settings,
        ifc_file,
        multiprocessing.cpu_count(),
        geometry_library=GEOMETRY_LIBRARY,  # type: ignore
    )
