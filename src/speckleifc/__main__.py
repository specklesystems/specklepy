from specklepy.api.operations import send
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.credentials import get_accounts_for_server
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models import Version
from specklepy.transports.server import ServerTransport

from speckleifc.importer import convert_file


def main() -> Version:
    PROJECT_ID = "f3a42bdf24"
    MODEL_ID = "0e23cfdea3"
    SERVER_URL = "app.speckle.systems"
    # FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\60mins.ifc"
    # FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\hillside_house_meters.ifc"
    FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\GRAPHISOFT_Archicad_Sample_Project-S-Office_v1.0_AC25.ifc"

    # Conversion
    data = convert_file(FILE)

    # Send to speckle
    account = get_accounts_for_server(SERVER_URL)[0]

    remote_transport = ServerTransport(PROJECT_ID, account=account)

    root_id = send(data, transports=[remote_transport])

    client = SpeckleClient()
    client.authenticate_with_account(account)

    create_version = CreateVersionInput(
        object_id=root_id, model_id=MODEL_ID, project_id=PROJECT_ID
    )
    version = client.version.create(create_version)

    return version


if __name__ == "__main__":
    main()
