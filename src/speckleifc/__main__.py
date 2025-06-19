import time

from specklepy.api.operations import send
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.credentials import get_accounts_for_server
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models import Version
from specklepy.transports.server import ServerTransport

from speckleifc.importer import convert_file

###

# TODO: tomorrow, either we optimise n-gon PR, or we throw it away.
# I'm hoping that POLYGONS_WITHOUT_HOLES is faster than TRIANGLES
# but nothing concretely confirmed
# tldr: send is not much slower in py from C#
# geometry itterator is pretty slow


def main() -> Version:
    PROJECT_ID = "f3a42bdf24"
    MODEL_ID = "0e23cfdea3"
    SERVER_URL = "app.speckle.systems"
    # FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\60mins.ifc"
    FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\hillside_house_meters.ifc"
    # FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\GRAPHISOFT_Archicad_Sample_Project-S-Office_v1.0_AC25.ifc"  # noqa: E501
    # FILE = "C:\\Users\\Jedd\\Desktop\\openshell\\GRAPHISOFT_Archicad_Sample_Project-S-Office_v1.0_AC25.ifc"  # noqa: E501

    start = time.time()
    data = convert_file(FILE)
    print(f"File conversion complete after {(time.time() - start) * 1000}ms")

    start = time.time()
    account = get_accounts_for_server(SERVER_URL)[0]

    remote_transport = ServerTransport(PROJECT_ID, account=account)

    root_id = send(data, transports=[remote_transport])
    print(f"Sending to speckle complete after: {(time.time() - start) * 1000}ms")

    start = time.time()
    client = SpeckleClient()
    client.authenticate_with_account(account)

    create_version = CreateVersionInput(
        object_id=root_id, model_id=MODEL_ID, project_id=PROJECT_ID
    )
    version = client.version.create(create_version)
    print(f"Version committed after: {(time.time() - start) * 1000}ms")

    return version


if __name__ == "__main__":
    main()
