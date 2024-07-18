from urllib.parse import quote, unquote, urlparse
from warnings import warn

from gql import gql

from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.credentials import (
    Account,
    get_account_from_token,
    get_accounts_for_server,
)
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning
from specklepy.transports.server.server import ServerTransport


class StreamWrapper:
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
    model_id: str = None
    _client: SpeckleClient = None
    _account: Account = None

    def __repr__(self):
        return (
            f"StreamWrapper( server: {self.host}, stream_id: {self.stream_id}, type:"
            f" {self.type} )"
        )

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

        if not segments or len(segments) < 2:
            raise SpeckleException(
                f"Cannot parse {url} into a stream wrapper class - invalid URL"
                " provided."
            )

        # check for fe2 URL
        if "/projects/" in parsed.path:
            use_fe2 = True
            key_stream = "project"
        else:
            use_fe2 = False
            key_stream = "stream"

        while segments:
            segment = segments.pop(0)

            if use_fe2 is False:
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
                        f"Cannot parse {url} into a stream wrapper class - invalid URL"
                        " provided."
                    )
            elif segments and use_fe2 is True:
                if segment.lower() == "projects":
                    self.stream_id = segments.pop(0)
                elif segment.lower() == "models":
                    next_segment = segments.pop(0)
                    if "," in next_segment:
                        raise SpeckleException("Multi-model urls are not supported yet")
                    elif unquote(next_segment).startswith("$"):
                        raise SpeckleException(
                            "Federation model urls are not supported"
                        )
                    elif len(next_segment) == 32:
                        self.object_id = next_segment
                    else:
                        self.branch_name = unquote(next_segment).split("@")[0]
                        if "@" in unquote(next_segment):
                            self.commit_id = unquote(next_segment).split("@")[1]

                else:
                    raise SpeckleException(
                        f"Cannot parse {url} into a stream wrapper class - invalid URL"
                        " provided."
                    )

        if use_fe2 is True and self.branch_name is not None:
            self.model_id = self.branch_name
            # get branch name
            query = gql(
                """
                query Project($project_id: String!, $model_id: String!) {
                    project(id: $project_id) {
                        id
                        model(id: $model_id) {
                            name
                        }
                    }
                }
            """
            )
            self._client = self.get_client()
            params = {"project_id": self.stream_id, "model_id": self.model_id}
            project = self._client.httpclient.execute(query, params)

            try:
                self.branch_name = project["project"]["model"]["name"]
            except KeyError as ke:
                raise SpeckleException("Project model name is not found", ke)

        if not self.stream_id:
            raise SpeckleException(
                f"Cannot parse {url} into a stream wrapper class - no {key_stream} id found."
            )

    @property
    def server_url(self):
        return f"{'https' if self.use_ssl else 'http'}://{self.host}"

    def get_account(self, token: str = None) -> Account:
        """
        Gets an account object for this server from the local accounts db
        (added via Speckle Manager or a json file)
        """
        if self._account and self._account.token:
            return self._account

        self._account = next(iter(get_accounts_for_server(self.host)), None)

        if not self._account:
            self._account = get_account_from_token(token, self.server_url)

        if self._client:
            self._client.authenticate_with_account(self._account)

        return self._account

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
        Gets a server transport for this stream using an authenticated client.
        If there is no local account for this
        server and the client was not authenticated with a token,
        this will throw an exception.

        Returns:
            ServerTransport -- constructed for this stream
            with a pre-authenticated client
        """
        if not self._account or not self._account.token:
            self.get_account(token)
        return ServerTransport(self.stream_id, account=self._account)

    def to_string(self) -> str:
        """
        Constructs a URL depending on the StreamWrapper type and FE version.
        """
        use_fe2 = False
        key_streams = "/streams/"
        key_branches = "/branches/"
        if isinstance(self.branch_name, str):
            value_branch = quote(self.branch_name)
            if self.branch_name == "globals":
                key_branches = "/"
        key_commits = "/commits/"
        if isinstance(self.commit_id, str) and self.branch_name == "globals":
            key_commits = "/globals/"
        key_objects = "/objects/"

        if "/projects/" in self.stream_url:
            use_fe2 = True
            key_streams = "/projects/"
            key_branches = "/models/"
            value_branch = self.model_id
            key_commits = "@"
            key_objects = "/models/"

        wrapper_type = self.type
        if use_fe2 is False or (use_fe2 is True and not self.model_id):
            base_url = f"{self.server_url}{key_streams}{self.stream_id}"
        else:  # fe2 is True and model_id available
            base_url = f"{self.server_url}{key_streams}{self.stream_id}{key_branches}{value_branch}"

        if wrapper_type == "object":
            return f"{base_url}{key_objects}{self.object_id}"
        elif wrapper_type == "commit":
            return f"{base_url}{key_commits}{self.commit_id}"
        elif wrapper_type == "branch":
            return f"{self.server_url}{key_streams}{self.stream_id}{key_branches}{value_branch}"
        elif wrapper_type == "stream":
            return f"{self.server_url}{key_streams}{self.stream_id}"
        else:
            raise SpeckleException(
                f"Cannot parse StreamWrapper of type '{wrapper_type}'"
            )
