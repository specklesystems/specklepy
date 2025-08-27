import json
import time
import traceback
from argparse import ArgumentParser
from os import getenv

from speckleifc.ifc_geometry_processing import open_ifc
from speckleifc.importer import ImportJob
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.credentials import Account, get_accounts_for_server
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models.current import Version
from specklepy.core.api.operations import send
from specklepy.transports.server import ServerTransport


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
    account = Account.from_token(TOKEN, SERVER_URL)

    try:
        version = open_and_convert_file(
            args.file_path,
            args.project_id,
            args.version_message,
            args.model_id,
            account,
        )
        with open(args.output_path, "w") as f:
            json.dump({"success": True, "commitId": version.id}, f)
    except Exception as e:
        error_msg = f"IFC Importer failed with exception:\n{traceback.format_exc()}"
        print(error_msg)

        # Write error result
        with open(args.output_path, "w") as f:
            json.dump({"success": False, "error": str(e)}, f)


def open_and_convert_file(
    file_path: str,
    project_id: str,
    version_message: str | None,
    model_id: str,
    account: Account,
) -> Version:
    start = time.time()
    very_start = start

    ifc_file = open_ifc(file_path)
    import_job = ImportJob(ifc_file)
    data = import_job.convert()

    print(f"File conversion complete after {(time.time() - start) * 1000}ms")

    start = time.time()

    remote_transport = ServerTransport(project_id, account=account)

    root_id = send(data, transports=[remote_transport], use_default_cache=False)
    print(f"Sending to speckle complete after: {(time.time() - start) * 1000}ms")

    start = time.time()
    server_url = account.serverInfo.url
    assert server_url
    client = SpeckleClient(host=server_url, use_ssl=server_url.startswith("https"))
    client.authenticate_with_account(account)

    create_version = CreateVersionInput(
        object_id=root_id,
        model_id=model_id,
        project_id=project_id,
        message=version_message,
        source_application="IFC",
    )
    version = client.version.create(create_version)
    end = time.time()
    print(f"Version committed after: {(end - start) * 1000}ms")

    print(f"Total time (to commit): {(end - very_start) * 1000}ms")
    del ifc_file

    return version


def manual_import() -> None:
    PROJECT_ID = "f3a42bdf24"
    MODEL_ID = "0e23cfdea3"
    SERVER_URL = "app.speckle.systems"
    # FILE_PATH = "C:\\Users\\Jedd\\Desktop\\openshell\\60mins.ifc"
    # FILE_PATH = "C:\\Users\\Jedd\\Desktop\\openshell\\hillside_house_meters.ifc"
    # FILE_PATH = "C:\\Users\\Jedd\\Desktop\\openshell\\GRAPHISOFT_Archicad_Sample_Project-S-Office_v1.0_AC25.ifc"  # noqa: E501
    # FILE_PATH = (
    #     "C:\\Test Files\\ifc\\GRAPHISOFT_Archicad_Sample_Project-S-Office_v1.0_AC25.ifc"  # noqa: E501
    # )
    FILE_PATH = "C:\\Test Files\\ifc\\Building-Architecture.ifc"  # noqa: E501

    account = get_accounts_for_server(SERVER_URL)[0]

    open_and_convert_file(FILE_PATH, PROJECT_ID, None, MODEL_ID, account)


if __name__ == "__main__":
    start = time.time()
    # cmd_line_import()
    manual_import()
    print(f"Total time (including cleanup): {(time.time() - start) * 1000}ms")
