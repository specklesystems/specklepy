from gql.transport import transport
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import (
    StreamWrapper,
    get_default_account,
    get_local_accounts,
)
from specklepy.api import operations

if __name__ == "__main__":
    # initialise the client
    xyz_client = SpeckleClient(host="speckle.xyz")  # or whatever your host is
    # client = SpeckleClient(host="localhost:3000", use_ssl=False) or use local server

    # authenticate the client with a token
    xyz_client.authenticate(
        token=[acc for acc in get_local_accounts() if acc.userInfo.id != "4d722975bc"][
            0
        ].token
    )

    stream = xyz_client.stream.get(id="81d2f2c135")
    print(stream)

    local_client = SpeckleClient(host="localhost:3000", use_ssl=False)
    local_client.authenticate(
        token=[acc for acc in get_local_accounts() if acc.userInfo.id == "4d722975bc"][
            0
        ].token
    )

    local_stream_id = local_client.stream.create(stream.name)
    print(local_stream_id)

    remote_commits = xyz_client.commit.list(stream.id)

    local_wrapper = StreamWrapper(f"http://localhost:3000/streams/{local_stream_id}")

    for remote_commit in remote_commits:
        xyz_wrapper = StreamWrapper(
            f"https://speckle.xyz/streams/{stream.id}/commits/{remote_commit.id}"
        )

        received_object = operations.receive(
            remote_commit.referencedObject, xyz_wrapper.get_transport()
        )

        sent_object_id = operations.send(
            received_object, [local_wrapper.get_transport()]
        )

        commit_id = local_client.commit.create(local_stream_id, sent_object_id)

        # xyz_client.object.get()

        print(commit_id)
