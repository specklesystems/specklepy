from __future__ import annotations

import logging
from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

from speckleifc.ifc_geometry_processing import open_ifc  # noqa: E402

_LOGGER = "speckleifc.ifc_geometry_processing"


def _step_file(tmp_path: Path, schema: str) -> Path:
    path = tmp_path / "model.ifc"
    path.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        "FILE_NAME('model.ifc','2026-01-01T00:00:00',(''),(''),'','','');\n"
        f"FILE_SCHEMA(('{schema}'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=IFCPROJECT('0YvctVUKr0kugbFTf53O9L',$,'P',$,$,$,$,$,$);\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    )
    return path


@pytest.mark.parametrize("schema", ["IFC2X3", "IFC4", "IFC4X3_ADD2"])
def test_open_ifc_logs_the_schema_identifier(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, schema: str
):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        open_ifc(str(_step_file(tmp_path, schema)))

    (record,) = [r for r in caplog.records if r.name == _LOGGER]
    assert getattr(record, "ifc.schema_identifier") == schema
