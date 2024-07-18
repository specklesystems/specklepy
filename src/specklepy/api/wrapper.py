from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import Account
from specklepy.core.api.wrapper import StreamWrapper as CoreStreamWrapper
from specklepy.logging import metrics
from specklepy.transports.server.server import ServerTransport


class StreamWrapper(CoreStreamWrapper):
    """
    The `StreamWrapper` gives you some handy helpers to deal with urls and
    get authenticated clients and transports.

    Construct a `StreamWrapper` with a stream, branch, commit, or object URL.
    The corresponding ids will be stored
    in the wrapper. If you have local accounts on the machine,
    you can use the `get_account` and `get_client` methods
    to get a local account for the server. You can also pass a token into `get_client`
    if you don't have a corresponding
    local account for the server.

    ```py
    from specklepy.api.wrapper import StreamWrapper

    # provide any stream, branch, commit, object, or globals url
    wrapper = StreamWrapper("https://app.speckle.systems/streams/3073b96e86/commits/604bea8cc6")

    # get an authenticated SpeckleClient if you have a local account for the server
    client = wrapper.get_client()

    # get an authenticated ServerTransport if you have a local account for the server
    transport = wrapper.get_transport()
    ```
    """

    stream_url: str = None
    use_ssl: bool = True
    host: str = None
    stream_id: str = None
    commit_id: str = None
    object_id: str = None
    branch_name: str = None
    _client: SpeckleClient = None
    _account: Account = None

    def __init__(self, url: str) -> None:
        super().__init__(url=url)

    def get_account(self, token: str = None) -> Account:
        """
        Gets an account object for this server from the local accounts db
        (added via Speckle Manager or a json file)
        """
        metrics.track(metrics.SDK, custom_props={"name": "Stream Wrapper Get Account"})
        return super().get_account(token)

    def get_client(self, token: str = None) -> SpeckleClient:
        """
        Gets an authenticated client for this server.
        You may provide a token if there aren't any local accounts on this
        machine. If no account is found and no token is provided,
        an unauthenticated client is returned.

        Arguments:
            token {str}
            -- optional token if no local account is available (defaults to None)

        Returns:
            SpeckleClient
            -- authenticated with a corresponding local account or the provided token
        """
        metrics.track(metrics.SDK, custom_props={"name": "Stream Wrapper Get Client"})
        return super().get_client(token)

    def get_transport(self, token: str = None) -> ServerTransport:
        """
        Gets a server transport for this stream using an authenticated client.
        If there is no local account for this
        server and the client was not authenticated with a token,
        this will throw an exception.

        Returns:
            ServerTransport -- constructed for this stream
            with a pre-authenticated client
        """
        metrics.track(
            metrics.SDK, custom_props={"name": "Stream Wrapper Get Transport"}
        )
        return super().get_transport(token)
