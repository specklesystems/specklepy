from unittest.mock import MagicMock

import httpx
import pytest

from speckle_automate import AutomationContext
from speckle_automate.schema import (
    AutomationRunData,
    VersionCreationTrigger,
    VersionCreationTriggerPayload,
)


def make_ctx(server_url: str) -> AutomationContext:
    run_data = AutomationRunData(
        project_id="p",
        speckle_server_url=server_url,
        automation_id="a",
        automation_run_id="r",
        function_run_id="f",
        triggers=[
            VersionCreationTrigger(
                trigger_type="versionCreation",
                payload=VersionCreationTriggerPayload(model_id="m", version_id="v"),
            )
        ],
    )
    return AutomationContext(automation_run_data=run_data, speckle_client=MagicMock())


@pytest.mark.parametrize(
    "server_url", ["https://app.speckle.systems/", "https://app.speckle.systems"]
)
def test_file_result_url(server_url: str) -> None:
    assert (
        make_ctx(server_url).file_result_url("b1")
        == "https://app.speckle.systems/api/stream/p/blob/b1"
    )


def test_store_file_result_logs_the_download_link(tmp_path, monkeypatch, capsys):
    ctx = make_ctx("https://app.speckle.systems/")
    path = tmp_path / "report.zip"
    path.write_bytes(b"zip")
    response = MagicMock()
    response.raise_for_status.return_value.json.return_value = {
        "uploadResults": [{"blobId": "b1", "fileName": "report.zip", "uploadStatus": 1}]
    }
    monkeypatch.setattr(httpx, "post", MagicMock(return_value=response))

    assert ctx.store_file_result(path) == "b1"
    assert (
        "Stored file result report.zip: "
        "https://app.speckle.systems/api/stream/p/blob/b1"
    ) in capsys.readouterr().out
