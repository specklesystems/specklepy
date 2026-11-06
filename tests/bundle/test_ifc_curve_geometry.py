"""ENG-11487 — products with no 3D representation get their curves as line geometry;
annotations and products with a body do not."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

api = pytest.importorskip("ifcopenshell.api")  # requires the [speckleifc] extra

from speckleifc.ifc_geometry_processing import open_ifc  # noqa: E402
from speckleifc.importer import ImportJob  # noqa: E402
from specklepy.bundle.spec import Rel  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "cube_with_distribution_system.ifc"
BASE = "curves"
CUBE_GUID = "18CFESN5fCsuplarC$2Ulg"


class _NoProgress:
    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def _add_curve_product(f, ifc_class: str, context, container):
    product = api.run("root.create_entity", f, ifc_class=ifc_class)
    api.run("geometry.edit_object_placement", f, product=product, matrix=None)
    points = [
        f.create_entity("IfcCartesianPoint", Coordinates=c)
        for c in ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    ]
    rep = f.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Axis",
        RepresentationType="Curve3D",
        Items=[f.create_entity("IfcPolyline", Points=points)],
    )
    api.run("geometry.assign_representation", f, product=product, representation=rep)
    api.run(
        "spatial.assign_container", f, products=[product], relating_structure=container
    )
    return product


def test_curve_only_products_get_polyline_geometry(tmp_path):
    f = open_ifc(str(FIXTURE))
    context = next(
        c
        for c in f.by_type("IfcGeometricRepresentationContext")
        if c.ContextType == "Model"
    )
    container = f.by_guid(CUBE_GUID).ContainedInStructure[0].RelatingStructure
    proxy = _add_curve_product(f, "IfcBuildingElementProxy", context, container)
    annotation = _add_curve_product(f, "IfcAnnotation", context, container)

    job = ImportJob(f, str(tmp_path), BASE, _NoProgress())
    job.run()
    assert job.curve_geometries_count == 1

    con = duckdb.connect()
    g = f"read_parquet('{tmp_path}/{BASE}"

    def displayed_types(guid: str) -> list[str]:
        return [
            r[0]
            for r in con.execute(
                f"""
                SELECT geo.type
                FROM {g}.eav.objects.parquet') o
                JOIN {g}.envelope.relations.parquet') i
                  ON i.src = o.object_index AND i.rel = ?
                JOIN {g}.envelope.nodes.parquet') n ON n.id = i.dst
                JOIN {g}.envelope.relations.parquet') d
                  ON d.src = n.def_ref AND d.rel = ?
                JOIN {g}.geometries.parquet') geo ON geo.geometryIndex = d.dst
                WHERE o.application_id = ?
                """,
                [int(Rel.DISPLAY_INSTANCE), int(Rel.DEFINES), guid],
            ).fetchall()
        ]

    assert displayed_types(proxy.GlobalId) == ["polyline"]
    assert displayed_types(annotation.GlobalId) == []
    assert "polyline" not in displayed_types(CUBE_GUID)
