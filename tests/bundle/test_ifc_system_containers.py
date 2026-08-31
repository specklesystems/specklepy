"""ENG-9181 — IFC systems must land as ``MEP System`` containers in Parquet.

Converts the checked-in fixture (the material-names cube plus an
``IfcDistributionSystem`` grouping it via ``IfcRelAssignsToGroup``) through the
native import path (``ImportJob.run()`` driving a ``BundleBuilder``), then asserts
the container row uses the catalogued ``MEP System`` subtype — the same tag
rvextract/nwextract emit — and that the member has exactly one ``IN_SYSTEM`` edge
targeting it.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

FIXTURE = Path(__file__).parent / "fixtures" / "cube_with_distribution_system.ifc"
BASE = "sysfixture"
CUBE_GUID = "18CFESN5fCsuplarC$2Ulg"
SYSTEM_GUID = "1EXXO5mlv2GQbM_kriwNSo"


class _NoProgress:
    """Duck-typed stand-in for IngestionProgressManager (no server in this test)."""

    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def test_distribution_system_becomes_mep_system_container(tmp_path):
    from speckleifc.converter.node import MEP_SYSTEM_SUBTYPE
    from speckleifc.ifc_geometry_processing import open_ifc
    from speckleifc.importer import ImportJob
    from specklepy.bundle import BundleBuilder, Producer
    from specklepy.bundle.spec import NodeKind, Rel

    builder = BundleBuilder(Producer("ifc", "0.8.5"), "m", str(tmp_path), BASE)
    ImportJob(open_ifc(str(FIXTURE)), builder, _NoProgress()).run()
    builder.build()

    con = duckdb.connect()
    g = f"read_parquet('{tmp_path}/{BASE}"

    # one CONTAINER row, catalogued subtype, IFC type folded into the label
    sysrows = con.execute(
        f"SELECT id, name, subtype FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.CONTAINER)} AND subtype = ?",
        [MEP_SYSTEM_SUBTYPE],
    ).fetchall()
    assert len(sysrows) == 1
    assert sysrows[0][1] == "HVAC Supply (AIRCONDITIONING)"

    # the cube has exactly one IN_SYSTEM edge and it targets that container
    cube_k = con.execute(
        f"SELECT object_index FROM {g}.eav.objects.parquet') WHERE application_id = ?",
        [CUBE_GUID],
    ).fetchone()[0]
    in_system = con.execute(
        f"SELECT src, dst FROM {g}.envelope.relations.parquet') WHERE rel = ?",
        [int(Rel.IN_SYSTEM)],
    ).fetchall()
    assert in_system == [(cube_k, sysrows[0][0])]

    # spatial containers keep their raw IFC class names as subtype
    subtypes = {
        r[0]
        for r in con.execute(
            f"SELECT subtype FROM {g}.envelope.nodes.parquet') "
            f"WHERE kind = {int(NodeKind.CONTAINER)}"
        ).fetchall()
    }
    assert "IfcProject" in subtypes
