import os

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from specklepy.api.credentials import Account
from specklepy.api.models.current import ServerInfo
from specklepy.bundle.download import (
    BundleReference,
    download_bundle,
    is_bare_file_name,
)
from specklepy.logging.exceptions import SpeckleException

LISTING = "/api/v2/projects/p/models/m/versions/v/artifacts"


def _account(httpserver: HTTPServer) -> Account:
    return Account(token="secret", serverInfo=ServerInfo(url=httpserver.url_for("")))


def _serve(httpserver: HTTPServer, names: list[str]) -> None:
    files = []
    for name in names:
        httpserver.expect_request(f"/blob/{name}").respond_with_data(
            f"content of {name}".encode()
        )
        files.append({"name": name, "url": httpserver.url_for(f"/blob/{name}")})
    httpserver.expect_request(
        LISTING, headers={"Authorization": "Bearer secret"}
    ).respond_with_json({"files": files})


def test_bundle_reference_parsing():
    ref = BundleReference.parse("bundle.p.m.v")
    assert (ref.project_id, ref.model_id, ref.version_id) == ("p", "m", "v")
    assert str(ref) == "bundle.p.m.v"
    assert BundleReference.is_reference(
        "bundle.x"
    ) and not BundleReference.is_reference("abc123")
    with pytest.raises(ValueError):
        BundleReference.parse("bundle.p.m")
    with pytest.raises(ValueError):
        BundleReference.parse("bundle.p..v")
    with pytest.raises(ValueError):
        BundleReference.parse("deadbeef")


def test_bare_file_names():
    assert is_bare_file_name("v.eav.eav.parquet")
    for bad in ("", ".", "..", "../x", "a/b", "a\\b", "C:x", None):
        assert not is_bare_file_name(bad)


def test_downloads_every_listed_file(httpserver: HTTPServer, tmp_path):
    names = ["v.eav.eav.parquet", "v.geometries.parquet", "v.geometries.1.parquet"]
    _serve(httpserver, names)
    paths = download_bundle(_account(httpserver), "p", "m", "v", str(tmp_path))
    assert [os.path.basename(p) for p in paths] == names
    assert (tmp_path / "v.geometries.1.parquet").read_bytes() == (
        b"content of v.geometries.1.parquet"
    )
    blob_requests = [r for r, _ in httpserver.log if r.path.startswith("/blob/")]
    assert all("Authorization" not in r.headers for r in blob_requests)


def test_skips_geometry_and_viewer_files(httpserver: HTTPServer, tmp_path):
    _serve(
        httpserver,
        ["v.eav.eav.parquet", "v.geometries.parquet", "v.viewer.dat", "v.viewer.idx"],
    )
    paths = download_bundle(
        _account(httpserver), "p", "m", "v", str(tmp_path), include_geometry=False
    )
    assert [os.path.basename(p) for p in paths] == ["v.eav.eav.parquet"]


def test_404_means_no_bundle(httpserver: HTTPServer, tmp_path):
    httpserver.expect_request(LISTING).respond_with_response(Response(status=404))
    assert download_bundle(_account(httpserver), "p", "m", "v", str(tmp_path)) == []
    assert not os.path.exists(tmp_path / "anything")


def test_other_errors_raise(httpserver: HTTPServer, tmp_path):
    httpserver.expect_request(LISTING).respond_with_response(
        Response("nope", status=403)
    )
    with pytest.raises(SpeckleException, match="403"):
        download_bundle(_account(httpserver), "p", "m", "v", str(tmp_path))


def test_rejects_unsafe_names(httpserver: HTTPServer, tmp_path):
    httpserver.expect_request(LISTING).respond_with_json(
        {"files": [{"name": "../escape.parquet", "url": httpserver.url_for("/x")}]}
    )
    with pytest.raises(SpeckleException, match="invalid file name"):
        download_bundle(_account(httpserver), "p", "m", "v", str(tmp_path))
