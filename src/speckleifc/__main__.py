import json
import time
import traceback
from argparse import ArgumentParser
from os import getenv

from speckleifc.main import open_and_convert_file
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.credentials import get_accounts_for_server
from specklepy.logging import metrics


def cmd_line_import() -> None:
    parser = ArgumentParser(
        prog="speckleifc",
        description="imports a file",
    )
    parser.add_argument("file_path")
    parser.add_argument("output_path")
    parser.add_argument("project_id")
    parser.add_argument("version_message")
    parser.add_argument("model_id")
    # parser.add_argument("model_name")
    # parser.add_argument("region_name")

    args = parser.parse_args()

    TOKEN = getenv("USER_TOKEN")
    assert TOKEN is not None
    SERVER_URL = getenv("SPECKLE_SERVER_URL") or "http://127.0.0.1:3000"

    metrics.set_host_app(
        "ifc",
    )

    try:
        client = SpeckleClient(SERVER_URL, use_ssl=not SERVER_URL.startswith("http://"))
        client.authenticate_with_token(TOKEN)
        project = client.project.get(args.project_id)

        version = open_and_convert_file(
            args.file_path,
            project,
            args.version_message,
            args.model_id,
            client,
        )
        with open(args.output_path, "w") as f:
            json.dump({"success": True, "commitId": version.id}, f)
    except Exception as e:
        error_msg = f"IFC Importer failed with exception:\n{traceback.format_exc()}"
        print(error_msg)

        # Write error result
        with open(args.output_path, "w") as f:
            json.dump({"success": False, "error": str(e)}, f)


def manual_import() -> None:
    PROJECT_ID = "f3a42bdf24"
    MODEL_ID = "0e23cfdea3"
    SERVER_URL = "app.speckle.systems"
    FILE_PATH = "C:\\Test Files\\Non-conf\\objects_R25_IFC4x3.ifc"  # noqa: E501

    metrics.set_host_app(
        "ifc",
    )

    account = get_accounts_for_server(SERVER_URL)[0]
    client = SpeckleClient(SERVER_URL, use_ssl=not SERVER_URL.startswith("http://"))
    client.authenticate_with_account(account)
    project = client.project.get(PROJECT_ID)

    open_and_convert_file(FILE_PATH, project, None, MODEL_ID, client)


if __name__ == "__main__":
    start = time.time()
    # cmd_line_import()

    manual_import()
    print(f"Total time (including cleanup): {(time.time() - start) * 1000}ms")
