"""ArtifactPipeline HTTP contract: sign → presigned PUT → complete against fake
transports, pinning which headers each rail carries."""

import json

import httpx
import pytest

from specklepy.api.credentials import Account
from specklepy.bundle.upload import ArtifactPipeline
from specklepy.logging import metrics

VERSION_ID = "ver123"


@pytest.fixture
def pipeline(tmp_path):
    artefact = tmp_path / "bundle.envelope.parquet"
    artefact.write_bytes(b"parquet-bytes")

    account = Account.from_token("secret-token", "https://speckle.example.org")
    speckle_requests: list[httpx.Request] = []
    s3_requests: list[httpx.Request] = []

    def speckle_handler(request: httpx.Request) -> httpx.Response:
        speckle_requests.append(request)
        if request.url.path.endswith("/uploads/sign"):
            return httpx.Response(
                200,
                json={
                    "uploads": {
                        artefact.name: {"url": "https://s3.example.org/put/bundle"}
                    }
                },
            )
        if request.url.path.endswith("/uploads/complete"):
            return httpx.Response(200, json={"versionId": VERSION_ID})
        raise AssertionError(f"unexpected speckle request: {request.url}")

    def s3_handler(request: httpx.Request) -> httpx.Response:
        s3_requests.append(request)
        return httpx.Response(200, headers={"ETag": '"abc"'})

    with ArtifactPipeline(
        project_id="proj",
        ingestion_id="ing",
        version_id=VERSION_ID,
        account=account,
        output_dir=str(tmp_path),
    ) as p:
        p._speckle._transport = httpx.MockTransport(speckle_handler)
        p._s3._transport = httpx.MockTransport(s3_handler)
        result = p.upload_files(
            {artefact.name: str(artefact)}, root_id="root", total_children_count=1
        )

    assert result == VERSION_ID
    return speckle_requests, s3_requests


def test_speckle_requests_carry_client_app_headers(pipeline):
    # The server derives clientAppVersion for envelope-born versions from
    # these headers on uploads/complete (ENG-9491).
    speckle_requests, _ = pipeline
    assert len(speckle_requests) == 2  # sign + complete
    for request in speckle_requests:
        assert request.headers["apollographql-client-name"] == metrics.HOST_APP
        assert (
            request.headers["apollographql-client-version"] == metrics.HOST_APP_VERSION
        )
        assert request.headers["authorization"] == "Bearer secret-token"


def test_presigned_s3_put_carries_no_speckle_headers(pipeline):
    _, s3_requests = pipeline
    assert len(s3_requests) == 1
    (put,) = s3_requests
    assert "apollographql-client-name" not in put.headers
    assert "apollographql-client-version" not in put.headers
    assert "authorization" not in put.headers


def test_upload_dir_finds_artefacts_when_base_name_has_glob_metachars(tmp_path):
    """FEA-645: the base name is the source filename stem, and `[a29]`-style tags
    turn an unescaped glob into a character class — the artefacts were written but
    never found. The `[a]`-matching decoy proves the match is literal."""
    base = "Tower [a29] ?rev* v2"
    (tmp_path / f"{base}.nodes.parquet").write_bytes(b"nodes")
    (tmp_path / f"{base}.geometries.parquet").write_bytes(b"geo")
    (tmp_path / "Tower a ?rev* v2.nodes.parquet").write_bytes(b"decoy")
    signed: list[list[str]] = []

    def speckle_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/uploads/sign"):
            files = json.loads(request.content)["files"]
            signed.append(files)
            return httpx.Response(
                200,
                json={
                    "uploads": {
                        f: {"url": f"https://s3.example.org/put/{i}"}
                        for i, f in enumerate(files)
                    }
                },
            )
        if request.url.path.endswith("/uploads/complete"):
            return httpx.Response(200, json={"versionId": VERSION_ID})
        raise AssertionError(f"unexpected speckle request: {request.url}")

    def s3_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"ETag": '"abc"'})

    account = Account.from_token("secret-token", "https://speckle.example.org")
    with ArtifactPipeline(
        project_id="proj",
        ingestion_id="ing",
        version_id=VERSION_ID,
        account=account,
        output_dir=str(tmp_path),
    ) as p:
        p._speckle._transport = httpx.MockTransport(speckle_handler)
        p._s3._transport = httpx.MockTransport(s3_handler)
        result = p.upload_dir(base, root_id="root", total_children_count=2)

    assert result == VERSION_ID
    assert signed == [[f"{base}.geometries.parquet", f"{base}.nodes.parquet"]]
