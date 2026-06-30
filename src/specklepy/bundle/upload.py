"""Speckle 4.0 artefact upload pipeline (server v2 data endpoints).

Port of the .NET ``ArtifactPipeline``. Uploads a client-built artefact bundle (the parquet
triple — geometries + eav.* + envelope.*) via the v2 endpoints: ``sign`` → presigned PUT
per file → ``complete`` (which creates the version). Fully independent of the v1 send path.

The endpoints are **filename-keyed and count-agnostic**: ``sign`` takes the list of artefact
basenames, the server presigns one PUT per name under ``versions/{versionId}/{name}``, and
``complete`` verifies the etags and creates the commit with ``id = versionId``. The version
id is **pre-allocated by the server at ingestion creation**, so artefact filenames can bake
it in before any bytes exist.
"""

from __future__ import annotations

import glob
import os
from typing import Mapping

import httpx

from specklepy.core.api.credentials import Account


class ArtifactUploadError(Exception):
    pass


def _parse_etag(response: httpx.Response) -> str:
    etag = response.headers.get("etag", "")
    return etag.strip().strip('"')


class ArtifactPipeline:
    """Uploads an already-built artefact bundle via the v2 sign → PUT → complete flow."""

    def __init__(
        self,
        project_id: str,
        ingestion_id: str,
        version_id: str,
        account: Account,
        output_dir: str,
        timeout: float = 120.0,
    ) -> None:
        self._project_id = project_id
        self._ingestion_id = ingestion_id
        self.version_id = version_id
        self.output_dir = output_dir

        base = account.serverInfo.url.rstrip("/") + "/api/v2/"
        headers = {"Authorization": f"Bearer {account.token}"} if account.token else {}
        self._speckle = httpx.Client(base_url=base, headers=headers, timeout=timeout)
        # presigned S3 PUTs are unauthenticated (the URL carries the signature).
        self._s3 = httpx.Client(timeout=timeout)

    def upload_files(
        self,
        file_name_to_path: Mapping[str, str],
        root_id: str,
        total_children_count: int,
    ) -> str:
        """Upload a bundle (basename → local path) and complete the version. Returns the version id."""
        signed = self._sign(list(file_name_to_path.keys()))
        uploads = signed.get("uploads", {})

        etags: dict[str, str] = {}
        for name, path in file_name_to_path.items():
            presigned = uploads.get(name)
            if presigned is None:
                raise ArtifactUploadError(
                    f"Server did not sign an upload for file '{name}'"
                )
            etags[name] = self._upload_file(path, presigned)

        return self._complete(etags, root_id, total_children_count)

    def upload_dir(
        self, base_name: str, root_id: str, total_children_count: int
    ) -> str:
        """Convenience: upload every ``{base_name}.*.parquet`` artefact in :attr:`output_dir`."""
        files = {
            os.path.basename(p): p
            for p in sorted(
                glob.glob(os.path.join(self.output_dir, f"{base_name}.*.parquet"))
            )
        }
        if not files:
            raise ArtifactUploadError(
                f"No artefact files found for base '{base_name}' in {self.output_dir}"
            )
        return self.upload_files(files, root_id, total_children_count)

    def close(self) -> None:
        self._speckle.close()
        self._s3.close()

    def __enter__(self) -> ArtifactPipeline:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ── internals ──────────────────────────────────────────────────────────

    def _sign(self, files: list[str]) -> dict:
        uri = f"projects/{self._project_id}/modelingestion/{self._ingestion_id}/uploads/sign"
        resp = self._speckle.post(uri, json={"files": files})
        self._ensure_success(resp, "artifacts sign")
        return resp.json()

    def _upload_file(self, file_path: str, presigned: Mapping) -> str:
        url = presigned["url"]
        extra = presigned.get("additionalRequestHeaders") or {}
        headers = {"Content-Type": "application/octet-stream", **extra}
        with open(file_path, "rb") as f:
            resp = self._s3.put(url, content=f.read(), headers=headers)
        resp.raise_for_status()
        return _parse_etag(resp)

    def _complete(
        self, etags: Mapping[str, str], root_id: str, total_children_count: int
    ) -> str:
        uri = f"projects/{self._project_id}/modelingestion/{self._ingestion_id}/uploads/complete"
        resp = self._speckle.post(
            uri,
            json={
                "etags": dict(etags),
                "rootId": root_id,
                "totalChildrenCount": total_children_count,
            },
        )
        self._ensure_success(resp, "artifacts complete")

        # The version id is pre-allocated (server-minted at ingestion creation) and is the commit
        # PK the server just completed against — authoritative. If the server echoes a versionId it
        # must match; a mismatch means we'd point at the wrong version, so fail loudly.
        echoed = None
        try:
            echoed = resp.json().get("versionId")
        except Exception:  # noqa: BLE001 - body may legitimately be empty
            echoed = None
        if echoed is not None and echoed != self.version_id:
            raise ArtifactUploadError(
                f"Server completed version '{echoed}' but the pre-allocated id was '{self.version_id}'."
            )
        return self.version_id

    @staticmethod
    def _ensure_success(response: httpx.Response, operation: str) -> None:
        if response.is_success:
            return
        raise ArtifactUploadError(
            f"{operation} failed with {response.status_code}: {response.text}"
        )
