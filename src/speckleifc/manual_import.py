import time

from speckleifc.main import open_and_convert_file
from specklepy.api.client import SpeckleClient
from specklepy.core.api.credentials import get_accounts_for_server
from specklepy.logging import metrics


def _manual_import() -> None:
    from specklepy.core.api.inputs.model_ingestion_inputs import (
        ModelIngestionCreateInput,
        SourceDataInput,
    )

    PROJECT_ID = "412a3c3927"
    MODEL_ID = "223e61212d"
    SERVER_URL = "latest.speckle.systems"
    FILE_PATH = r"C:\Test Files\ifc\AC20-FZK-Haus.ifc"  # noqa: E501

    metrics.set_host_app(
        "ifc",
    )

    account = get_accounts_for_server(SERVER_URL)[0]
    client = SpeckleClient(SERVER_URL, use_ssl=not SERVER_URL.startswith("http://"))
    client.authenticate_with_account(account)

    ingestion = client.model_ingestion.create(
        ModelIngestionCreateInput(
            model_id=MODEL_ID,
            project_id=PROJECT_ID,
            progress_message="",
            source_data=SourceDataInput(
                source_application_slug="speckleifc",
                source_application_version="0.0.0",
                file_name=None,
                file_size_bytes=None,
            ),
            max_idle_timeout_seconds=2700,  # 45mins
        )
    )
    project = client.project.get(PROJECT_ID)

    open_and_convert_file(FILE_PATH, project, None, ingestion.id, client)


if __name__ == "__main__":
    start = time.time()

    _manual_import()
    print(f"Total time (including cleanup): {(time.time() - start):.3f}s")
