from unittest.mock import MagicMock

import httpx
import pytest

from specklepy.logging.exceptions import SpeckleException
from tests.unit.speckle_automate.test_attach_result_to_objects import (
    _minimal_automation_context,
)


def context(server_url: str = "https://app.speckle.systems/"):
    ctx = _minimal_automation_context()
    ctx.automation_run_data.speckle_server_url = server_url
    return ctx


def upload_answers(monkeypatch, **result):
    response = MagicMock()
    response.raise_for_status.return_value.json.return_value = {
        "uploadResults": [{"blobId": "b1", "fileName": "report.zip", **result}]
    }
    post = MagicMock(return_value=response)
    monkeypatch.setattr(httpx, "post", post)
    return post


@pytest.mark.parametrize(
    "server_url", ["https://app.speckle.systems/", "https://app.speckle.systems"]
)
def test_file_result_url(server_url: str) -> None:
    assert (
        context(server_url).file_result_url("b1")
        == "https://app.speckle.systems/api/stream/p/blob/b1"
    )


def test_store_file_result_logs_the_download_link(tmp_path, monkeypatch, capsys):
    ctx = context("https://app.speckle.systems")
    (path := tmp_path / "report.zip").write_bytes(b"zip")
    post = upload_answers(monkeypatch, uploadStatus=1)

    assert ctx.store_file_result(path) == "b1"
    assert post.call_args.args[0] == "https://app.speckle.systems/api/stream/p/blob"
    assert (
        "Stored file result report.zip: "
        "https://app.speckle.systems/api/stream/p/blob/b1"
    ) in capsys.readouterr().out
    assert ctx._automation_result.blobs == ["b1"]


def test_store_file_result_raises_when_the_server_rejected_the_file(
    tmp_path, monkeypatch, capsys
):
    ctx = context()
    (path := tmp_path / "report.zip").write_bytes(b"zip")
    upload_answers(monkeypatch, uploadStatus=2, uploadError="File size limit reached")

    with pytest.raises(SpeckleException, match="File size limit reached"):
        ctx.store_file_result(path)
    assert "Stored file result" not in capsys.readouterr().out
    assert ctx._automation_result.blobs == []
