"""Publish a :class:`BundleBuilder` as a new version over the model-ingestion rail."""

from __future__ import annotations

import contextlib
import shutil
import traceback
from dataclasses import dataclass

from specklepy.api.credentials import Account
from specklepy.bundle.builder import BundleBuilder
from specklepy.bundle.download import BundleReference
from specklepy.bundle.upload import ArtifactPipeline
from specklepy.logging.exceptions import SpeckleException


@dataclass(frozen=True)
class SendOptions:
    message: str | None = None
    file_name: str | None = None
    file_size_bytes: int | None = None
    max_idle_timeout_seconds: int = 600
    keep_files: bool = False


@dataclass(frozen=True)
class SendResult:
    project_id: str
    model_id: str
    version_id: str
    ingestion_id: str
    object_count: int

    @property
    def bundle_reference(self) -> str:
        return str(BundleReference(self.project_id, self.model_id, self.version_id))


def send(
    account: Account,
    project_id: str,
    model_id: str,
    builder: BundleBuilder,
    options: SendOptions | None = None,
) -> SendResult:
    """Create the ingestion (the server pre-allocates the version id), build and re-key
    the bundle, upload it, and return. The builder is finished by this call."""
    from specklepy.api.client import SpeckleClient
    from specklepy.api.inputs.model_ingestion_inputs import (
        ModelIngestionCreateInput,
        ModelIngestionFailedInput,
        SourceDataInput,
    )

    options = options or SendOptions()
    url = account.serverInfo.url or ""
    client = SpeckleClient(host=url, use_ssl=url.startswith("https"))
    client.authenticate_with_account(account)
    producer = builder.producer
    ingestion = client.model_ingestion.create(
        ModelIngestionCreateInput(
            model_id=model_id,
            project_id=project_id,
            progress_message=options.message
            or f"Sending from {producer.slug} {producer.version}",
            source_data=SourceDataInput(
                source_application_slug=producer.slug,
                source_application_version=producer.version,
                file_name=options.file_name,
                file_size_bytes=options.file_size_bytes,
            ),
            max_idle_timeout_seconds=options.max_idle_timeout_seconds,
        )
    )
    try:
        version_id = client.model_ingestion.get_reserved_version_id(
            project_id, ingestion.id
        )
        if not version_id:
            raise SpeckleException(
                f"The server at '{url}' did not pre-allocate a version id for the "
                "ingestion; bundle upload requires a server with the /api/v2 data "
                "endpoints."
            )
        files = builder.build().rename_to(version_id)
        root_id = str(BundleReference(project_id, model_id, version_id))
        with ArtifactPipeline(
            project_id, ingestion.id, version_id, account, files.directory
        ) as upload:
            committed = upload.upload_files(files.by_name, root_id, files.object_count)
        if not options.keep_files:
            shutil.rmtree(files.directory, ignore_errors=True)
        return SendResult(
            project_id, model_id, committed, ingestion.id, files.object_count
        )
    except BaseException as error:
        with contextlib.suppress(Exception):
            client.model_ingestion.fail_with_error(
                ModelIngestionFailedInput(
                    ingestion_id=ingestion.id,
                    project_id=project_id,
                    error_reason=str(error),
                    error_stacktrace=traceback.format_exc(),
                )
            )
        raise
