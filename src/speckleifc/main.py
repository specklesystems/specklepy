import contextlib
import importlib.metadata
import tempfile
import time
import traceback
from pathlib import Path

from speckleifc.ifc_geometry_processing import open_ifc
from speckleifc.importer import ImportJob
from specklepy.api.client import SpeckleClient
from specklepy.api.inputs.model_ingestion_inputs import (
    ModelIngestionFailedInput,
    ModelIngestionStartProcessingInput,
    SourceDataInput,
)
from specklepy.api.models.current import Project
from specklepy.bundle.builder import BundleBuilder
from specklepy.bundle.download import BundleReference
from specklepy.bundle.envelope_writer import Producer
from specklepy.bundle.upload import ArtifactPipeline
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from specklepy.progress.ingestion_progress import IngestionProgressManager

# Since progress messages are currently blocking (no async), we're being extra coarse
# with progress updates to ensure we're not waisting time sending updates.
# We could maybe go a little lower, but for now I'm not risking degrading performance
PROGRESS_INTERVAL_SECONDS = 10


def _bundle_producer() -> Producer:
    try:
        version = importlib.metadata.version("ifcopenshell")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    return Producer(slug="ifc", version=version)


def open_and_convert_file(
    file_path: str,
    project: Project,
    version_message: str | None,
    model_ingestion_id: str,
    client: SpeckleClient,
) -> str:
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

        # The bundle basename is the server-reserved version id; resolving it before
        # conversion also fails fast on servers without the v2 data endpoints.
        version_id = client.model_ingestion.get_reserved_version_id(
            project.id, model_ingestion_id
        )
        if not version_id:
            raise SpeckleException(
                "Model ingestion returned no pre-allocated version id — the server "
                "must support the v2 data endpoints to ingest IFC bundles."
            )

        progress.report("Opening file", None)
        ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]

        with tempfile.TemporaryDirectory(prefix="speckle-bundle-") as bundle_dir:
            builder = BundleBuilder(_bundle_producer(), "m", bundle_dir, version_id)
            ImportJob(ifc_file, builder, progress).run()  # pyright: ignore[reportUnknownArgumentType]
            files = builder.build()
            print(f"File conversion complete after {(time.time() - start):.3f}s")

            start = time.time()
            progress.report("Uploading bundle", None)
            root_id = str(BundleReference(project.id, ingestion.model_id, version_id))
            with ArtifactPipeline(
                project.id, model_ingestion_id, version_id, account, bundle_dir
            ) as pipeline:
                version_id = pipeline.upload_files(
                    files.by_name, root_id, files.object_count
                )

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
        )

        return version_id
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
