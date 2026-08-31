"""ENG-9129 regression — authored IFC material names must survive into Parquet.

Converts the checked-in IFC fixture through the native import path and asserts the
MATERIAL rows carry names. The fixture has no IFCSURFACESTYLE, so ifcopenshell falls
back to its default style — with ``use-material-names`` on, that must land as
``DefaultMaterial`` on the MATERIAL node instead of NULL.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

FIXTURE = (
    Path(__file__).parents[1] / "integration" / "client" / "current" / "test_file.ifc"
)
BASE = "fixture"


class _NoProgress:
    """Duck-typed stand-in for IngestionProgressManager (no server in this test)."""

    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def test_material_names_land_on_material_nodes(tmp_path):
    from speckleifc.ifc_geometry_processing import open_ifc
    from speckleifc.importer import ImportJob
    from specklepy.bundle.spec import NodeKind, Rel

    ImportJob(open_ifc(str(FIXTURE)), str(tmp_path), BASE, _NoProgress()).run()

    con = duckdb.connect()
    g = f"read_parquet('{tmp_path}/{BASE}"

    rows = con.execute(
        f"SELECT name, argb, opacity FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.MATERIAL)}"
    ).fetchall()

    assert rows, "fixture must produce at least one MATERIAL row"
    assert all(name for name, *_ in rows)
    assert any(name == "DefaultMaterial" for name, *_ in rows)
    assert all(argb is not None and opacity is not None for _, argb, opacity in rows)

    # every material is bound geometry-plane only (HAS_MATERIAL src = geometry)
    rels = con.execute(f"SELECT rel FROM {g}.envelope.relations.parquet')").fetchall()
    emitted = {r[0] for r in rels}
    assert int(Rel.HAS_MATERIAL) in emitted
    assert int(Rel.OBJECT_HAS_MATERIAL) not in emitted
    assert int(Rel.NODE_HAS_MATERIAL) not in emitted
