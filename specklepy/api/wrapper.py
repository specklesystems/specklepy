from warnings import warn
from urllib.parse import urlparse, unquote
from specklepy.api.credentials import (
    Account,
    get_account_from_token,
    get_local_accounts,
)
from specklepy.logging import metrics
from specklepy.api.client import SpeckleClient
from specklepy.transports.server.server import ServerTransport
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning


class StreamWrapper:
    """
    The `StreamWrapper` gives you some handy helpers to deal with urls and get authenticated clients and transports.

    Construct a `StreamWrapper` with a stream, branch, commit, or object URL. The corresponding ids will be stored
    in the wrapper. If you have local accounts on the machine, you can use the `get_account` and `get_client` methods
    to get a local account for the server. You can also pass a token into `get_client` if you don't have a corresponding
    local account for the server.

    ```py
    from specklepy.api.wrapper import StreamWrapper

    # provide any stream, branch, commit, object, or globals url
    wrapper = StreamWrapper("https://speckle.xyz/streams/3073b96e86/commits/604bea8cc6")

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

    def __repr__(self):
        return f"StreamWrapper( server: {self.host}, stream_id: {self.stream_id}, type: {self.type} )"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def type(self) -> str:
        if self.object_id:
            return "object"
        elif self.commit_id:
            return "commit"
        elif self.branch_name:
            return "branch"
        else:
            return "stream" if self.stream_id else "invalid"

    def __init__(self, url: str) -> None:
        self.stream_url = url
        parsed = urlparse(url)
        self.host = parsed.netloc
        self.use_ssl = parsed.scheme == "https"
        segments = parsed.path.strip("/").split("/", 3)
        metrics.track(metrics.STREAM_WRAPPER, self.get_account())

        if not segments or len(segments) < 2:
            raise SpeckleException(
                f"Cannot parse {url} into a stream wrapper class - invalid URL provided."
            )

        while segments:
            segment = segments.pop(0)
            if segments and segment.lower() == "streams":
                self.stream_id = segments.pop(0)
            elif segments and segment.lower() == "commits":
                self.commit_id = segments.pop(0)
            elif segments and segment.lower() == "branches":
                self.branch_name = unquote(segments.pop(0))
            elif segments and segment.lower() == "objects":
                self.object_id = segments.pop(0)
            elif segment.lower() == "globals":
                self.branch_name = "globals"
                if segments:
                    self.commit_id = segments.pop(0)
            else:
                raise SpeckleException(
                    f"Cannot parse {url} into a stream wrapper class - invalid URL provided."
                )

        if not self.stream_id:
            raise SpeckleException(
                f"Cannot parse {url} into a stream wrapper class - no stream id found."
            )

    @property
    def server_url(self):
        return f"{'https' if self.use_ssl else 'http'}://{self.host}"

    def get_account(self, token: str = None) -> Account:
        """
        Gets an account object for this server from the local accounts db (added via Speckle Manager or a json file)
        """
        if self._account and self._account.token:
            return self._account

        self._account = next(
            (a for a in get_local_accounts() if self.host in a.serverInfo.url),
            None,
        )

        if not self._account:
            self._account = get_account_from_token(token, self.server_url)

        if self._client:
            self._client.authenticate_with_account(self._account)

        return self._account

    def get_client(self, token: str = None) -> SpeckleClient:
        """
        Gets an authenticated client for this server. You may provide a token if there aren't any local accounts on this
        machine. If no account is found and no token is provided, an unauthenticated client is returned.

        Arguments:
            token {str} -- optional token if no local account is available (defaults to None)

        Returns:
            SpeckleClient -- authenticated with a corresponding local account or the provided token
        """
        if self._client and token is None:
            return self._client

        if not self._account or not self._account.token:
            self.get_account(token)

        if not self._client:
            self._client = SpeckleClient(host=self.host, use_ssl=self.use_ssl)

        if self._account.token is None and token is None:
            warn(f"No local account found for server {self.host}", SpeckleWarning)
            return self._client

        if self._account.token:
            self._client.authenticate_with_account(self._account)
        else:
            self._client.authenticate_with_token(token)

        return self._client

    def get_transport(self, token: str = None) -> ServerTransport:
        """
        Gets a server transport for this stream using an authenticated client. If there is no local account for this
        server and the client was not authenticated with a token, this will throw an exception.

        Returns:
            ServerTransport -- constructed for this stream with a pre-authenticated client
        """
        if not self._account or not self._account.token:
            self.get_account(token)
        return ServerTransport(self.stream_id, account=self._account)
