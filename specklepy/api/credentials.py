import os
from warnings import warn
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import urlparse, unquote
from specklepy.logging import metrics
from specklepy.api.models import ServerInfo
from specklepy.api.client import SpeckleClient
from specklepy.transports.sqlite import SQLiteTransport
from specklepy.transports.server.server import ServerTransport
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning


class UserInfo(BaseModel):
    name: str
    email: str
    company: Optional[str]
    id: str


class Account(BaseModel):
    isDefault: bool = None
    token: str
    refreshToken: str = None
    serverInfo: ServerInfo
    userInfo: UserInfo
    id: str = None

    def __repr__(self) -> str:
        return f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url}, isDefault: {self.isDefault})"

    def __str__(self) -> str:
        return self.__repr__()


def get_local_accounts(base_path: str = None) -> List[Account]:
    """Gets all the accounts present in this environment

    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        List[Account] -- list of all local accounts or an empty list if no accounts were found
    """
    metrics.track(metrics.ACCOUNT_LIST)
    account_storage = SQLiteTransport(scope="Accounts", base_path=base_path)
    json_path = os.path.join(account_storage._base_path, "Accounts")
    os.makedirs(json_path, exist_ok=True)
    json_acct_files = [file for file in os.listdir(json_path) if file.endswith(".json")]

    accounts = []
    res = account_storage.get_all_objects()
    if res:
        accounts.extend(Account.parse_raw(r[1]) for r in res)
    if json_acct_files:
        try:
            accounts.extend(
                Account.parse_file(os.path.join(json_path, json_file))
                for json_file in json_acct_files
            )
        except Exception as ex:
            raise SpeckleException(
                "Invalid json accounts could not be read. Please fix or remove them.",
                ex,
            )

    return accounts


def get_default_account(base_path: str = None) -> Account:
    """Gets this environment's default account if any. If there is no default, the first found will be returned and set as default.
    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        Account -- the default account or None if no local accounts were found
    """
    metrics.track(metrics.ACCOUNT_DEFAULT)
    accounts = get_local_accounts(base_path=base_path)
    if not accounts:
        return None

    default = next((acc for acc in accounts if acc.isDefault), None)
    if not default:
        default = accounts[0]
        default.isDefault = True

    return default


class StreamWrapper:
    """
    The `StreamWrapper` gives you some handy helpers to deal with urls and get authenticated clients and transports.

    Construct a `StreamWrapper` with a stream, branch, commit, or object URL. The corresponding ids will be stored
    in the wrapper. If you have local accounts on the machine, you can use the `get_account` and `get_client` methods
    to get a local account for the server. You can also pass a token into `get_client` if you don't have a corresponding
    local account for the server.

    ```py
    from specklepy.api.credentials import StreamWrapper

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
        metrics.track("streamwrapper")
        self.stream_url = url
        parsed = urlparse(url)
        self.host = parsed.netloc
        self.use_ssl = parsed.scheme == "https"
        segments = parsed.path.strip("/").split("/", 3)

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

    def get_account(self) -> Account:
        """
        Gets an account object for this server from the local accounts db (added via Speckle Manager or a json file)
        """
        if self._account:
            return self._account

        self._account = next(
            (a for a in get_local_accounts() if self.host in a.serverInfo.url),
            None,
        )

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

        if not self._account:
            self.get_account()

        if not self._client:
            self._client = SpeckleClient(host=self.host, use_ssl=self.use_ssl)

        if self._account is None and token is None:
            warn(f"No local account found for server {self.host}", SpeckleWarning)
            return self._client

        self._client.authenticate(self._account.token if self._account else token)

        return self._client

    def get_transport(self, token: str = None) -> ServerTransport:
        """
        Gets a server transport for this stream using an authenticated client. If there is no local account for this
        server and the client was not authenticated with a token, this will throw an exception.

        Returns:
            ServerTransport -- constructed for this stream with a pre-authenticated client
        """
        if not self._client or not self._client.me:
            self.get_client(token)
        return ServerTransport(self.stream_id, self._client)
