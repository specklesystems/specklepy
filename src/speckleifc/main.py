import contextlib
import importlib.metadata
import os
import time
import traceback
from pathlib import Path

from speckleifc.ifc_geometry_processing import open_ifc
from speckleifc.importer import ImportJob
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionFailedInput,
    ModelIngestionStartProcessingInput,
    ModelIngestionSuccessInput,
    SourceDataInput,
)
from specklepy.core.api.models.current import Project, Version
from specklepy.core.api.operations import send
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from specklepy.progress.ingestion_progress import IngestionProgressManager
from specklepy.progress.progress_transport import ProgressTransport
from specklepy.transports.server import ServerTransport

# Since progress messages are currently blocking (no async), we're being extra coarse
# with progress updates to ensure we're not waisting time sending updates.
# We could maybe go a little lower, but for now I'm not risking degrading performance
PROGRESS_INTERVAL_SECONDS = 10

# Opt in to the Speckle 4.0 artefact bundle (parquet eav + envelope + geometries,
# uploaded via the v2 data endpoints) by setting SPECKLE_IFC_BUNDLE=1. Default is the v1
# detached-object send, whose behaviour is unchanged. Only flip where the target server
# exposes the v2 data endpoints AND the viewer reads bundles.
_BUNDLE_ENV_VAR = "SPECKLE_IFC_BUNDLE"


def _bundle_enabled() -> bool:
    return os.environ.get(_BUNDLE_ENV_VAR, "").strip().lower() in ("1", "true", "yes")


def open_and_convert_file(
    file_path: str,
    project: Project,
    version_message: str | None,
    model_ingestion_id: str,
    client: SpeckleClient,
) -> Version:
    try:
        start = time.time()
        very_start = start
        path = Path(file_path)

        specklepy_version = importlib.metadata.version("specklepy")
        ingestion = client.model_ingestion.start_processing(
            ModelIngestionStartProcessingInput(
                project_id=project.id,
                ingestion_id=model_ingestion_id,
                progress_message="Importing IFC file",
                source_data=SourceDataInput(
                    file_name=path.name,
                    file_size_bytes=path.stat().st_size,
                    source_application_slug=metrics.HOST_APP,
                    source_application_version=specklepy_version,
                ),
            )
        )
        progress = IngestionProgressManager(
            client, ingestion, PROGRESS_INTERVAL_SECONDS
        )
        account = client.account
        server_url = account.serverInfo.url
        assert server_url

        bundle = _bundle_enabled()

        progress.report("Opening file", None)
        ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]

        # Topology (system membership + port connectivity) is attached only for the
        # bundle path; the v1 output is left exactly as before.
        import_job = ImportJob(ifc_file, progress, emit_topology=bundle)  # pyright: ignore[reportUnknownArgumentType]
        data = import_job.convert()

        print(
            f"File conversion complete after {(time.time() - start):.3f}s"  # noqa: E501
        )

        start = time.time()

        if bundle:
            version = _upload_bundle(
                client, project, account, model_ingestion_id, data, progress
            )
        else:
            progress.report("Uploading objects", None)
            remote_transport = ServerTransport(project.id, account=account)
            progress_transport = ProgressTransport(progress)
            root_id = send(
                data,
                transports=[remote_transport, progress_transport],
                use_default_cache=False,
            )
            print(
                f"Sending to speckle complete after: {(time.time() - start):.3f}s"  # noqa: E501
            )

            start = time.time()

            version_id = client.model_ingestion.complete(
                ModelIngestionSuccessInput(
                    project_id=project.id,
                    ingestion_id=model_ingestion_id,
                    root_object_id=root_id,
                    version_message=version_message,
                )
            )

            # needed to query version until ingestion api expands to serve it
            version = client.version.get(version_id, project.id)

        end = time.time()
        print(f"Version committed after: {(end - start):.3f}s")

        print(f"Total time (to commit): {(end - very_start):.3f}s")
        del ifc_file

        custom_properties = {"ui": "dui3", "actionSource": "import"}
        if project.workspace_id:
            custom_properties["workspace_id"] = project.workspace_id

        metrics.track(
            metrics.SEND,
            account,
            custom_properties,
            send_sync=True,
            track_email=True,
        )

        return version
    except Exception as e:
        stack_trace = traceback.format_exc()
        with contextlib.suppress(Exception):
            # make sure to not report process kills when we're cancelling
            client.model_ingestion.fail_with_error(
                ModelIngestionFailedInput(
                    project_id=project.id,
                    ingestion_id=model_ingestion_id,
                    error_reason=str(e),
                    error_stacktrace=stack_trace,
                )
            )
        raise e


def _fetch_pre_allocated_version_id(
    account, project_id: str, model_ingestion_id: str
) -> str | None:
    """Read the ingestion's pre-allocated ``versionId`` (a v2-only top-level field).

    Done with a dedicated GraphQL query rather than the shared model_ingestion resource:
    ``ModelIngestion.versionId`` only exists on servers with the v2 data endpoints, so
    selecting it in the SDK's standard ingestion queries would break older servers.
    Runs only on the bundle path (which targets a v2 server), so it is safe here.
    """
    import httpx

    url = account.serverInfo.url.rstrip("/") + "/graphql"
    headers = {"Authorization": f"Bearer {account.token}"} if account.token else {}
    query = (
        "query($p:String!,$i:ID!){ project(id:$p){ ingestion(id:$i){ versionId } } }"
    )
    resp = httpx.post(
        url,
        headers=headers,
        json={"query": query, "variables": {"p": project_id, "i": model_ingestion_id}},
        timeout=60,
    )
    body = resp.json()
    if body.get("errors"):
        raise SpeckleException(
            f"Failed to fetch pre-allocated version id: {body['errors']}"
        )
    ingestion = ((body.get("data") or {}).get("project") or {}).get("ingestion") or {}
    return ingestion.get("versionId")


def _upload_bundle(
    client: SpeckleClient,
    project: Project,
    account,
    model_ingestion_id: str,
    data,
    progress: IngestionProgressManager,
) -> Version:
    """Build the Speckle 4.0 artefact bundle and upload it via the v2 data endpoints.

    Opt-in via SPECKLE_IFC_BUNDLE. Imports the bundle producer lazily so the default v1
    path never pulls pyarrow/duckdb (the ``specklepy[bundle]`` extra). The version is
    created server-side by the v2 ``complete`` call (no v1
    ``model_ingestion.complete``).
    """
    # Lazy: keeps pyarrow/duckdb out of the import graph on the v1 path.
    import tempfile

    from speckleifc.bundle_exporter import IfcBundleExporter
    from specklepy.bundle.upload import ArtifactPipeline

    version_id = _fetch_pre_allocated_version_id(
        account, project.id, model_ingestion_id
    )
    if not version_id:
        raise SpeckleException(
            "Model ingestion returned no pre-allocated version id — the server must "
            f"support the v2 data endpoints to use {_BUNDLE_ENV_VAR}."
        )

    progress.report("Writing bundle", None)
    with tempfile.TemporaryDirectory(prefix="speckle-bundle-") as bundle_dir:
        root_id, child_count = IfcBundleExporter(bundle_dir, version_id).export(data)
        progress.report("Uploading bundle", None)
        with ArtifactPipeline(
            project.id, model_ingestion_id, version_id, account, bundle_dir
        ) as pipeline:
            version_id = pipeline.upload_dir(version_id, root_id, child_count)

    # needed to query version until ingestion api expands to serve it
    return client.version.get(version_id, project.id)
