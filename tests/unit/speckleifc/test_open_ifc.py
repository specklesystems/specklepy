import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")

from speckleifc.ifc_geometry_processing import open_ifc  # noqa: E402


def _write_ifc(tmp_path: Path, schema: str, extension: str = ".ifc") -> Path:
    contents = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('synthetic schema regression'),'2;1');
FILE_NAME('synthetic.ifc','',(),(),'','','');
FILE_SCHEMA(('{schema}'));
ENDSEC;
DATA;
#1=IFCCARTESIANPOINT((0.,0.,0.));
ENDSEC;
END-ISO-10303-21;
"""
    source = tmp_path / f"synthetic{extension}"
    if extension == ".ifczip":
        with ZipFile(source, "w") as archive:
            archive.writestr("synthetic.ifc", contents)
    else:
        source.write_text(contents)
    return source


def _open_rejected_ifc(source: Path) -> dict:
    # ENG-10539: failed IfcOpenShell wrappers can raise during GC in pytest's hook.
    # Exercise the real parser in a child process to isolate its native cleanup.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json
import sys
from speckleifc.ifc_geometry_processing import open_ifc

try:
    open_ifc(sys.argv[1])
except Exception as error:
    print("RESULT_JSON:" + json.dumps({
        "type": type(error).__name__,
        "message": str(error),
        "cause_type": type(error.__cause__).__name__,
        "cause_message": str(error.__cause__),
    }))
else:
    raise AssertionError("Expected the file to be rejected")
""",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(
        next(
            line.removeprefix("RESULT_JSON:")
            for line in result.stdout.splitlines()
            if line.startswith("RESULT_JSON:")
        )
    )


@pytest.mark.parametrize("extension", [".ifc", ".ifczip"])
def test_legacy_schema_explains_reexport_without_modifying_input(tmp_path, extension):
    source = _write_ifc(tmp_path, "IFC20_LONGFORM", extension)
    original = source.read_bytes()

    failure = _open_rejected_ifc(source)

    assert failure["type"] == "SchemaError"
    message = failure["message"]
    assert "Unsupported schema: IFC20_LONGFORM" in message
    assert "legacy IFC 2.0" in message
    assert "Re-export the model as IFC2X3 or IFC4" in message
    assert "application that supports the original schema" in message
    assert "Changing only the FILE_SCHEMA header does not convert the model" in message
    assert failure["cause_type"] == "SchemaError"
    assert failure["cause_message"] == "Unsupported schema: IFC20_LONGFORM"
    assert source.read_bytes() == original


def test_unknown_schema_retains_identifier_and_explains_reexport(tmp_path):
    source = _write_ifc(tmp_path, "IFC_UNKNOWN")

    failure = _open_rejected_ifc(source)

    assert failure["type"] == "SchemaError"
    assert "Unsupported schema: IFC_UNKNOWN" in failure["message"]
    assert "Re-export the model as IFC2X3 or IFC4" in failure["message"]
    assert "legacy IFC 2.0" not in failure["message"]


@pytest.mark.parametrize("schema", ["IFC2X3", "IFC4", "IFC4X3_ADD2"])
def test_supported_schema_still_opens(tmp_path, schema):
    source = _write_ifc(tmp_path, schema)

    result = open_ifc(str(source))

    assert isinstance(result, ifcopenshell.file)
    assert result.schema_identifier == schema
    assert result.by_id(1).Coordinates == (0.0, 0.0, 0.0)


def test_missing_file_remains_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_ifc(str(tmp_path / "missing.ifc"))


def test_malformed_file_remains_a_file_open_error(tmp_path):
    source = tmp_path / "malformed.ifc"
    source.write_text("This is not an IFC file")

    failure = _open_rejected_ifc(source)

    assert failure["type"] == "SpeckleException"
    assert "File could not be opened as an IFC file" in failure["message"]
