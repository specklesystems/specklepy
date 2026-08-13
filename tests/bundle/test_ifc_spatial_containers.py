"""ENG-9180 — the IFC spatial hierarchy must land as canonical ``Collection``
containers; spaces ship as objects only.

Converts the checked-in fixture (a cube inside a full IfcProject > IfcSite >
IfcBuilding > IfcBuildingStorey > IfcSpace chain, the cube contained in the
space) through the real import path (``ImportJob.convert()``) and the Parquet
path (``IfcBundleExporter``), then asserts no container row carries an IFC
class name as its subtype, the space mints no container at all, and the cube's
occupancy rides as an IN_ROOM edge to the space *object* — while every spatial
element keeps its IFC class queryable as the ``ifcType`` eav row.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

FIXTURE = Path(__file__).parent / "fixtures" / "spatial_hierarchy.ifc"
BASE = "spatialfixture"
PROJECT_GUID = "3WoDmit2L9H8xguu5dNQPk"
SITE_GUID = "0RSW$KKbzCZ9VmSQg9Zwvf"
BUILDING_GUID = "1fOYmUWu5FGA6WZZJzE67P"
STOREY_GUID = "2GNgSHJ5j9BRUjqT$7tE8w"
SPACE_GUID = "0f2ZFZxLj3H9NC3$ruwqnu"
CUBE_GUID = "18CFESN5fCsuplarC$2Ulg"


class _NoProgress:
    """Duck-typed stand-in for IngestionProgressManager (no server in this test)."""

    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def test_spatial_hierarchy_lands_as_canonical_containers(tmp_path):
    from speckleifc.bundle_exporter import COLLECTION_SUBTYPE, IfcBundleExporter
    from speckleifc.ifc_geometry_processing import open_ifc
    from speckleifc.importer import ImportJob
    from specklepy.bundle.spec import NODE_KINDS, NodeKind, Rel

    root = ImportJob(open_ifc(str(FIXTURE)), _NoProgress()).convert()
    IfcBundleExporter(str(tmp_path), BASE).export(root)

    con = duckdb.connect()
    g = f"read_parquet('{tmp_path}/{BASE}"

    def k_of(app_id):
        return con.execute(
            f"SELECT object_index FROM {g}.eav.objects.parquet') "
            "WHERE application_id = ?",
            [app_id],
        ).fetchone()[0]

    def ifc_type_of(app_id):
        return con.execute(
            f"SELECT e.value_string FROM {g}.eav.eav.parquet') e "
            f"JOIN {g}.eav.paths.parquet') p USING (path_index) "
            f"JOIN {g}.eav.objects.parquet') o USING (object_index) "
            "WHERE p.path = 'ifcType' AND o.application_id = ?",
            [app_id],
        ).fetchone()[0]

    containers = con.execute(
        f"SELECT id, name, subtype, def_ref FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.CONTAINER)}"
    ).fetchall()

    # project/site/building/storey mint containers; the space does NOT
    assert {r[1] for r in containers} == {
        "SpatialDemo",
        "Default Site",
        "Default Building",
        "Ground Floor",
    }

    # every emitted subtype is the canonical catalogued tag — no IFC class names
    assert {r[2] for r in containers} == {COLLECTION_SUBTYPE}
    container_kind = next(r for r in NODE_KINDS if r.id == int(NodeKind.CONTAINER))
    assert COLLECTION_SUBTYPE in container_kind.subtype_values.split(",")

    # the def_ref parent chain IS the spatial hierarchy
    by_name = {r[1]: r for r in containers}
    assert by_name["SpatialDemo"][3] is None
    assert by_name["Default Site"][3] == by_name["SpatialDemo"][0]
    assert by_name["Default Building"][3] == by_name["Default Site"][0]
    assert by_name["Ground Floor"][3] == by_name["Default Building"][0]

    # spatial elements keep their IFC class queryable on the object rows
    for guid, ifc_type in [
        (SITE_GUID, "IfcSite"),
        (BUILDING_GUID, "IfcBuilding"),
        (STOREY_GUID, "IfcBuildingStorey"),
        (SPACE_GUID, "IfcSpace"),
        (CUBE_GUID, "IfcBuildingElementProxy"),
    ]:
        assert ifc_type_of(guid) == ifc_type

    rels = set(
        con.execute(
            f"SELECT rel, src, dst FROM {g}.envelope.relations.parquet')"
        ).fetchall()
    )
    storey_container_k = by_name["Ground Floor"][0]
    space_k, cube_k = k_of(SPACE_GUID), k_of(CUBE_GUID)

    # the space object and the cube both attach to the storey container...
    assert (int(Rel.IN_COLLECTION), space_k, storey_container_k) in rels
    assert (int(Rel.IN_COLLECTION), cube_k, storey_container_k) in rels

    # ...and occupancy rides as IN_ROOM: cube -> space object, exactly once
    in_room = [r for r in rels if r[0] == int(Rel.IN_ROOM)]
    assert in_room == [(int(Rel.IN_ROOM), cube_k, space_k)]

    # the storey still drives the level axis: the cube is ON_LEVEL
    assert any(r[0] == int(Rel.ON_LEVEL) and r[1] == cube_k for r in rels)
