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
    ModelIngestionUpdateInput,
    SourceDataInput,
)
from specklepy.core.api.models.current import Project, Version
from specklepy.core.api.operations import send
from specklepy.logging import metrics
from specklepy.transports.server import ServerTransport


def open_and_convert_file(
    file_path: str,
    project: Project,
    version_message: str,
    model_ingestion_id: str,
    client: SpeckleClient,
) -> Version:
    try:
        start = time.time()
        very_start = start
        path = Path(file_path)

        specklepy_version = importlib.metadata.version("specklepy")
        client.model_ingestion.start_processing(
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

        account = client.account
        server_url = account.serverInfo.url
        assert server_url
        remote_transport = ServerTransport(project.id, account=account)

        ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]

        client.model_ingestion.update_progress(
            ModelIngestionUpdateInput(
                project_id=project.id,
                ingestion_id=model_ingestion_id,
                progress_message="Converting file",
                progress=None,
            )
        )
        import_job = ImportJob(ifc_file)  # pyright: ignore[reportUnknownArgumentType]
        data = import_job.convert()

        print(f"File conversion complete after {(time.time() - start) * 1000}ms")

        start = time.time()

        client.model_ingestion.update_progress(
            ModelIngestionUpdateInput(
                project_id=project.id,
                ingestion_id=model_ingestion_id,
                progress_message="Uploading objects",
                progress=None,
            )
        )
        root_id = send(data, transports=[remote_transport], use_default_cache=False)
        print(f"Sending to speckle complete after: {(time.time() - start) * 1000}ms")

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
        print(f"Version committed after: {(end - start) * 1000}ms")

        print(f"Total time (to commit): {(end - very_start) * 1000}ms")
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
