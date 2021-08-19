import os
from specklepy.transports.server.server import ServerTransport
from warnings import warn
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import urlparse, unquote
from specklepy.api.models import ServerInfo
from specklepy.api.client import SpeckleClient
from specklepy.transports.sqlite import SQLiteTransport
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
    accounts = get_local_accounts(base_path=base_path)
    if not accounts:
        return None

    default = next((acc for acc in accounts if acc.isDefault), None)
    if not default:
        default = accounts[0]
        default.isDefault = True

    return default


class StreamWrapper:
    stream_url: str = None
    use_ssl: bool = True
    host: str = None
    stream_id: str = None
    commit_id: str = None
    object_id: str = None
    branch_name: str = None
    client: SpeckleClient = None
    account: Account = None

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
        segments = parsed.path.strip("/").split("/")

        if not segments or len(segments) > 4 or len(segments) < 2:
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
        if self.account:
            return self.account

        self.account = next(
            (a for a in get_local_accounts() if self.host in a.serverInfo.url),
            None,
        )

        return self.account

    def get_client(self) -> SpeckleClient:
        if self.client:
            return self.client

        if not self.account:
            self.get_account()

        self.client = SpeckleClient(host=self.host, use_ssl=self.use_ssl)

        if self.account is None:
            warn(f"No local account found for server {self.host}", SpeckleWarning)
            return self.client

        self.client.authenticate(self.account.token)
        return self.client

    def get_transport(self) -> ServerTransport:
        if not self.client:
            self.get_client()
        return ServerTransport(self.client, self.stream_id)