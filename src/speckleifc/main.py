import time

from speckleifc.ifc_geometry_processing import open_ifc
from speckleifc.importer import ImportJob
from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models.current import Project, Version
from specklepy.core.api.operations import send
from specklepy.logging import metrics
from specklepy.transports.server import ServerTransport


def open_and_convert_file(
    file_path: str,
    project: Project,
    version_message: str | None,
    model_id: str,
    client: SpeckleClient,
) -> Version:
    start = time.time()
    very_start = start

    account = client.account
    server_url = account.serverInfo.url
    assert server_url
    remote_transport = ServerTransport(project.id, account=account)

    ifc_file = open_ifc(file_path)  # pyright: ignore[reportUnknownVariableType]
    import_job = ImportJob(ifc_file)  # pyright: ignore[reportUnknownArgumentType]
    data = import_job.convert()

    print(f"File conversion complete after {(time.time() - start) * 1000}ms")

    start = time.time()

    root_id = send(data, transports=[remote_transport], use_default_cache=False)
    print(f"Sending to speckle complete after: {(time.time() - start) * 1000}ms")

    start = time.time()

    create_version = CreateVersionInput(
        object_id=root_id,
        model_id=model_id,
        project_id=project.id,
        message=version_message,
        source_application="ifc",
    )
    version = client.version.create(create_version)
    end = time.time()
    print(f"Version committed after: {(end - start) * 1000}ms")

    print(f"Total time (to commit): {(end - very_start) * 1000}ms")
    del ifc_file

    custom_properties = {"ui": "dui3", "actionSource": "import"}
    if project.workspace_id:
        custom_properties["workspace_id"] = project.workspace_id
    metrics.track(metrics.SEND, account, custom_properties)

    return version
