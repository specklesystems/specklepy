"""ENG-11286 — elements with geometry that are not in the spatial structure must
still be converted, with no collection or level membership."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

FIXTURE = Path(__file__).parent / "fixtures" / "cube_with_distribution_system.ifc"
BASE = "uncontained"
CUBE_GUID = "18CFESN5fCsuplarC$2Ulg"


class _NoProgress:
    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def test_uncontained_element_is_converted_without_collection(tmp_path):
    from speckleifc.ifc_geometry_processing import open_ifc
    from speckleifc.importer import ImportJob
    from specklepy.bundle.spec import Rel

    ifc_file = open_ifc(str(FIXTURE))
    for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
        ifc_file.remove(rel)

    job = ImportJob(ifc_file, str(tmp_path), BASE, _NoProgress())
    job.run()
    assert job.uncontained_converted == 1

    con = duckdb.connect()
    g = f"read_parquet('{tmp_path}/{BASE}"

    cube_k = con.execute(
        f"SELECT object_index FROM {g}.eav.objects.parquet') WHERE application_id = ?",
        [CUBE_GUID],
    ).fetchone()[0]
    cube_rels = {
        r[0]
        for r in con.execute(
            f"SELECT rel FROM {g}.envelope.relations.parquet') WHERE src = ?",
            [cube_k],
        ).fetchall()
    }

    assert int(Rel.DISPLAY_INSTANCE) in cube_rels
    assert int(Rel.IN_SYSTEM) in cube_rels
    assert int(Rel.IN_COLLECTION) not in cube_rels
    assert int(Rel.ON_LEVEL) not in cube_rels

    property_rows = con.execute(
        f"SELECT count(*) FROM {g}.eav.eav.parquet') WHERE object_index = ?",
        [cube_k],
    ).fetchone()[0]
    assert property_rows > 0
