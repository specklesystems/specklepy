import os
from pydantic import BaseModel, Field
from typing import List, Optional
from specklepy.logging import metrics
from specklepy.api.models import ServerInfo
from specklepy.transports.sqlite import SQLiteTransport
from specklepy.logging.exceptions import SpeckleException


class UserInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    company: Optional[str]
    id: Optional[str]


class Account(BaseModel):
    isDefault: bool = False
    token: str = None
    refreshToken: str = None
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)
    userInfo: UserInfo = Field(default_factory=UserInfo)
    id: str = None

    def __repr__(self) -> str:
        return f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url}, isDefault: {self.isDefault})"

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_token(cls, token: str, server_url: str = None):
        acct = cls(token=token)
        acct.serverInfo.url = server_url
        return acct


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
    metrics.track(
        metrics.ACCOUNTS,
        next(
            (acc for acc in accounts if acc.isDefault),
            accounts[0] if accounts else None,
        ),
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
    metrics.initialise_tracker(default)

    return default


def get_account_from_token(token: str, server_url: str = None) -> Account:
    """Gets the local account for the token if it exists
    Arguments:
        token {str} -- the api token

    Returns:
        Account -- the local account with this token or a shell account containing just the token and url if no local account is found
    """
    accounts = get_local_accounts()
    if not accounts:
        return Account.from_token(token, server_url)

    acct = next((acc for acc in accounts if acc.token == token), None)
    if acct:
        return acct

    if server_url:
        url = server_url.lower()
        acct = next(
            (acc for acc in accounts if url in acc.serverInfo.url.lower()), None
        )
        if acct:
            return acct

    return Account.from_token(token, server_url)


class StreamWrapper:
    def __init__(self, url: str = None) -> None:
        raise SpeckleException(
            message="The StreamWrapper has moved as of v2.6.0! Please import from specklepy.api.wrapper",
            exception=DeprecationWarning,
        )
