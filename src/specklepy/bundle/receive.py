"""Receive a bundle-only version: download, parse, wrap in a :class:`Model`."""

from __future__ import annotations

import os
import shutil
import tempfile

from specklepy.api.credentials import Account
from specklepy.bundle.bundle_reader import read_bundle
from specklepy.bundle.download import download_bundle
from specklepy.bundle.model import Model
from specklepy.logging.exceptions import SpeckleException

SDK_SLUG = "specklepy"


def receive(
    account: Account,
    project_id: str,
    model_id: str,
    version_id: str,
    *,
    include_geometry: bool = True,
    mark_received: bool = True,
) -> Model:
    directory = tempfile.mkdtemp(prefix="speckle-bundle-")
    try:
        files = download_bundle(
            account,
            project_id,
            model_id,
            version_id,
            directory,
            include_geometry=include_geometry,
        )
        if not files:
            raise SpeckleException(
                f"Version '{version_id}' (model '{model_id}', project '{project_id}') "
                f"has no artefact bundle on '{account.serverInfo.url}': the server "
                "may not serve /api/v2 artifacts, the token cannot read the project, "
                "or the bundle has not been produced."
            )
        model = Model(
            project_id,
            model_id,
            version_id,
            directory,
            sorted(os.path.join(directory, f) for f in os.listdir(directory)),
            read_bundle(directory),
            geometry_downloaded=include_geometry,
        )
        if mark_received:
            _mark_received(account, project_id, version_id)
        return model
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise


def _mark_received(account: Account, project_id: str, version_id: str) -> None:
    from specklepy.api.client import SpeckleClient
    from specklepy.api.inputs.version_inputs import MarkReceivedVersionInput

    url = account.serverInfo.url or ""
    client = SpeckleClient(host=url, use_ssl=url.startswith("https"))
    client.authenticate_with_account(account)
    client.version.received(
        MarkReceivedVersionInput(
            version_id=version_id, project_id=project_id, source_application=SDK_SLUG
        )
    )
