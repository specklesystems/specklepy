import contextlib
import importlib.metadata
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
from specklepy.progress.ingestion_progress import IngestionProgressManager
from specklepy.progress.progress_transport import ProgressTransport
from specklepy.transports.server import ServerTransport

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
        remote_transport = ServerTransport(project.id, account=account)
        progress_transport = ProgressTransport(
            progress,
        )

        progress.report("Opening file", None)
        ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]

        import_job = ImportJob(ifc_file, progress)  # pyright: ignore[reportUnknownArgumentType]
        data = import_job.convert()

        print(
            f"File conversion complete after {(time.time() - start):.3f}s"  # noqa: E501
        )

        start = time.time()

        progress.report("Uploading objects", None)
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
