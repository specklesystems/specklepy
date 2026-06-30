import contextlib
import importlib.metadata
import tempfile
import time
import traceback
from pathlib import Path

from speckleifc.bundle_exporter import IfcBundleExporter
from speckleifc.ifc_geometry_processing import open_ifc
from speckleifc.importer import ImportJob
from specklepy.bundle.upload import ArtifactPipeline
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionFailedInput,
    ModelIngestionStartProcessingInput,
    SourceDataInput,
)
from specklepy.core.api.models.current import Project, Version
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from specklepy.progress.ingestion_progress import IngestionProgressManager

# Since progress messages are currently blocking (no async), we're being extra coarse
# with progress updates to ensure we're not waisting time sending updates.
# We could maybe go a little lower, but for now I'm not risking degrading performance
PROGRESS_INTERVAL_SECONDS = 10


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
        # The version id is pre-allocated by the server at ingestion creation; the 4.0
        # artefact bundle is uploaded under it via the v2 data endpoints (see below).
        version_id = ingestion.status_data.version_id
        if not version_id:
            raise SpeckleException(
                "Ingestion did not return a pre-allocated version id"
            )

        progress.report("Opening file", None)
        ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]

        import_job = ImportJob(ifc_file, progress)  # pyright: ignore[reportUnknownArgumentType]
        data = import_job.convert()

        print(
            f"File conversion complete after {(time.time() - start):.3f}s"  # noqa: E501
        )

        start = time.time()

        # Speckle 4.0: build the artefact bundle (eav + envelope + geometries parquet) from
        # the converted tree, then upload it via the v2 data endpoints (sign -> PUT -> complete,
        # which creates the version). Replaces the v1 detached-object send entirely.
        progress.report("Writing bundle", None)
        with tempfile.TemporaryDirectory(prefix="speckle-bundle-") as bundle_dir:
            exporter = IfcBundleExporter(bundle_dir, version_id)
            root_id, total_children_count = exporter.export(data)
            print(
                f"Bundle written after: {(time.time() - start):.3f}s"  # noqa: E501
            )

            start = time.time()
            progress.report("Uploading bundle", None)
            with ArtifactPipeline(
                project.id, model_ingestion_id, version_id, account, bundle_dir
            ) as pipeline:
                version_id = pipeline.upload_dir(
                    version_id, root_id, total_children_count
                )
        print(
            f"Uploading bundle complete after: {(time.time() - start):.3f}s"  # noqa: E501
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
