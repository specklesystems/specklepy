"""ENG-9129 regression — authored IFC material names must survive into Parquet.

Converts the checked-in IFC fixture through BOTH paths and compares materials:
the legacy path (``ImportJob.convert()`` → root Collection with
``renderMaterialProxies`` holding ``RenderMaterial``s) against the Parquet path
(``IfcBundleExporter`` → ``envelope.nodes.parquet`` MATERIAL rows). The fixture
has no IFCSURFACESTYLE, so ifcopenshell falls back to its default style — with
``use-material-names`` on, the legacy material is named ``DefaultMaterial``;
that exact name must land on the MATERIAL node instead of NULL.
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


def _signed_int32(argb: int) -> int:
    """Independent reimplementation of the argb column encoding (don't reuse the
    producer's helper — the test should disagree with it if it ever breaks)."""
    argb &= 0xFFFFFFFF
    return argb - 0x1_0000_0000 if argb >= 0x8000_0000 else argb


def test_material_names_and_values_match_legacy_tree(tmp_path):
    from speckleifc.bundle_exporter import IfcBundleExporter
    from speckleifc.ifc_geometry_processing import open_ifc
    from speckleifc.importer import ImportJob
    from specklepy.bundle.spec import NodeKind

    root = ImportJob(
        open_ifc(str(FIXTURE)), _NoProgress(), emit_topology=True
    ).convert()

    legacy = [proxy.value for proxy in root["renderMaterialProxies"]]
    assert legacy, "fixture must produce at least one render material"
    # the legacy path authors a name for every material in this fixture
    # (ifcopenshell's fallback style => "DefaultMaterial")
    assert all(m.name for m in legacy)
    assert any(m.name == "DefaultMaterial" for m in legacy)

    IfcBundleExporter(str(tmp_path), BASE).export(root)

    rows = (
        duckdb.connect()
        .execute(
            "SELECT name, argb, opacity, metalness, roughness "
            f"FROM read_parquet('{tmp_path}/{BASE}.envelope.nodes.parquet') "
            f"WHERE kind = {int(NodeKind.MATERIAL)}"
        )
        .fetchall()
    )

    # identity is the applicationId, never the display name: one MATERIAL row per
    # distinct legacy material id (no dedup or inflation by name)
    assert len(rows) == len({m.applicationId for m in legacy})

    expected = {
        (
            m.name,
            _signed_int32(int(m.diffuse)),
            float(m.opacity),
            float(m.metalness),
            float(m.roughness),
        )
        for m in legacy
    }
    assert {tuple(r) for r in rows} == expected
