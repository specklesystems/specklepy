"""Bundle reference parsing and `/api/v2` artifact download."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from specklepy.api.credentials import Account
from specklepy.logging.exceptions import SpeckleException

BUNDLE_REFERENCE_PREFIX = "bundle."


@dataclass(frozen=True)
class BundleReference:
    """``bundle.<projectId>.<modelId>.<versionId>`` — what a bundle-only version carries
    in ``referencedObject`` instead of an object hash."""

    project_id: str
    model_id: str
    version_id: str

    @staticmethod
    def is_reference(value: str | None) -> bool:
        return bool(value) and value.startswith(BUNDLE_REFERENCE_PREFIX)

    @classmethod
    def parse(cls, value: str) -> BundleReference:
        if not cls.is_reference(value):
            raise ValueError(f"'{value}' is not a bundle reference")
        parts = value[len(BUNDLE_REFERENCE_PREFIX) :].split(".")
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"malformed bundle reference '{value}'")
        return cls(*parts)

    def __str__(self) -> str:
        ids = f"{self.project_id}.{self.model_id}.{self.version_id}"
        return BUNDLE_REFERENCE_PREFIX + ids


def is_bare_file_name(name: str | None) -> bool:
    return (
        bool(name)
        and name not in (".", "..")
        and not any(c in name for c in "/\\:")
        and os.path.basename(name) == name
    )


def _wanted(name: str, include_geometry: bool) -> bool:
    if ".viewer." in name:
        return False
    is_shard = ".geometries" in name and name.endswith(".parquet")
    return include_geometry or not is_shard


def download_bundle(
    account: Account,
    project_id: str,
    model_id: str,
    version_id: str,
    dest_dir: str,
    *,
    include_geometry: bool = True,
    timeout: float = 120.0,
) -> list[str]:
    """Download a version's bundle files into ``dest_dir``; ``[]`` when the version has
    no bundle (404)."""
    base = (account.serverInfo.url or "").rstrip("/") + "/api/v2/"
    headers = {"Authorization": f"Bearer {account.token}"} if account.token else {}
    with httpx.Client(base_url=base, headers=headers, timeout=timeout) as speckle:
        response = speckle.get(
            f"projects/{project_id}/models/{model_id}/versions/{version_id}/artifacts"
        )
    if response.status_code == 404:
        return []
    if response.is_error:
        raise SpeckleException(
            f"Listing artifacts failed with {response.status_code}: {response.text}"
        )
    files = response.json().get("files") or []
    if not files:
        return []

    os.makedirs(dest_dir, exist_ok=True)
    paths: list[str] = []
    # presigned urls are already authorized; never send the Speckle token to storage
    with httpx.Client(timeout=timeout) as storage:
        for file in files:
            name = file.get("name")
            if not is_bare_file_name(name):
                raise SpeckleException(
                    f"Artifact listing contains an invalid file name '{name}'."
                )
            if not _wanted(name, include_geometry):
                continue
            path = os.path.join(dest_dir, name)
            with storage.stream("GET", file["url"]) as download:
                if download.is_error:
                    download.read()
                    raise SpeckleException(
                        f"Downloading artifact '{name}' failed with "
                        f"{download.status_code}: {download.text}"
                    )
                with open(path, "wb") as out:
                    for chunk in download.iter_bytes():
                        out.write(chunk)
            paths.append(path)
    return paths
