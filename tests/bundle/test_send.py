import importlib
import os
from types import SimpleNamespace

import pytest

from specklepy.api.credentials import Account
from specklepy.api.models.current import ServerInfo
from specklepy.bundle import BundleBuilder, Producer
from specklepy.logging.exceptions import SpeckleException

send_module = importlib.import_module("specklepy.bundle.send")
ACCOUNT = Account(token="t", serverInfo=ServerInfo(url="http://localhost:1"))


class FakeIngestion:
    def __init__(self, reserved: str | None = "ver-1"):
        self.reserved = reserved
        self.created = []
        self.failed = []

    def create(self, input):
        self.created.append(input)
        return SimpleNamespace(id="ing-1")

    def get_reserved_version_id(self, project_id, ingestion_id):
        return self.reserved

    def fail_with_error(self, input):
        self.failed.append(input)


class FakeUpload:
    calls = []

    def __init__(self, project_id, ingestion_id, version_id, account, output_dir):
        self.args = (project_id, ingestion_id, version_id, output_dir)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def upload_files(self, by_name, root_id, total_children_count):
        FakeUpload.calls.append(
            (self.args, sorted(by_name), root_id, total_children_count)
        )
        return self.args[2]


@pytest.fixture
def fakes(monkeypatch):
    ingestion = FakeIngestion()
    client = SimpleNamespace(
        model_ingestion=ingestion, authenticate_with_account=lambda account: None
    )
    monkeypatch.setattr("specklepy.api.client.SpeckleClient", lambda **kw: client)
    monkeypatch.setattr(send_module, "ArtifactPipeline", FakeUpload)
    FakeUpload.calls.clear()
    return ingestion


def _builder(tmp_path) -> BundleBuilder:
    b = BundleBuilder(Producer("test", "2.0"), "m", str(tmp_path))
    b.get_or_add_object("a").set_properties({}, name="A")
    b.get_or_add_object("b")
    return b


def test_send_creates_ingestion_renames_uploads_and_cleans_up(tmp_path, fakes):
    result = send_module.send(
        ACCOUNT,
        "p",
        "m",
        _builder(tmp_path),
        send_module.SendOptions(message="hello", file_name="x.ifc"),
    )
    assert result.version_id == "ver-1" and result.ingestion_id == "ing-1"
    assert result.object_count == 2
    assert result.bundle_reference == "bundle.p.m.ver-1"

    [created] = fakes.created
    assert created.progress_message == "hello"
    assert created.source_data.source_application_slug == "test"
    assert created.source_data.source_application_version == "2.0"
    assert created.source_data.file_name == "x.ifc"

    [(args, names, root_id, count)] = FakeUpload.calls
    assert args == ("p", "ing-1", "ver-1", str(tmp_path))
    assert all(n.startswith("ver-1.") for n in names) and len(names) >= 10
    assert root_id == "bundle.p.m.ver-1" and count == 2
    assert not os.path.exists(tmp_path)


def test_keep_files_and_default_message(tmp_path, fakes):
    send_module.send(
        ACCOUNT, "p", "m", _builder(tmp_path), send_module.SendOptions(keep_files=True)
    )
    assert os.path.exists(tmp_path / "ver-1.envelope.meta.parquet")
    assert fakes.created[0].progress_message == "Sending from test 2.0"


def test_missing_reserved_version_id_fails_the_ingestion(tmp_path, fakes):
    fakes.reserved = None
    with pytest.raises(SpeckleException, match="pre-allocate"):
        send_module.send(ACCOUNT, "p", "m", _builder(tmp_path))
    [failed] = fakes.failed
    assert failed.ingestion_id == "ing-1" and "pre-allocate" in failed.error_reason
    assert FakeUpload.calls == []


def test_upload_failure_fails_the_ingestion_and_reraises(tmp_path, fakes, monkeypatch):
    def boom(self, *args):
        raise RuntimeError("s3 down")

    monkeypatch.setattr(FakeUpload, "upload_files", boom)
    with pytest.raises(RuntimeError, match="s3 down"):
        send_module.send(ACCOUNT, "p", "m", _builder(tmp_path))
    assert fakes.failed[0].error_reason == "s3 down"
    assert os.path.exists(tmp_path)  # left for inspection, as C#
