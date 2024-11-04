import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from specklepy.core.api.models import ServerInfo
from specklepy.core.helpers import speckle_path_provider
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.sqlite import SQLiteTransport


class UserInfo(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None


class Account(BaseModel):
    isDefault: bool = False
    token: Optional[str] = None
    refreshToken: Optional[str] = None
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)
    userInfo: UserInfo = Field(default_factory=UserInfo)
    id: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url},"
            f" isDefault: {self.isDefault})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_token(cls, token: str, server_url: str = None):
        acct = cls(token=token)
        acct.serverInfo.url = server_url
        return acct


def get_local_accounts(base_path: Optional[str] = None) -> List[Account]:
    """Gets all the accounts present in this environment

    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        List[Account] -- list of all local accounts or an empty list if
        no accounts were found
    """
    accounts: List[Account] = []
    try:
        account_storage = SQLiteTransport(scope="Accounts", base_path=base_path)
        res = account_storage.get_all_objects()
        account_storage.close()
        if res:
            accounts.extend(Account.model_validate_json(r[1]) for r in res)
    except SpeckleException:
        # cannot open SQLiteTransport, probably because of the lack
        # of disk write permissions
        pass

    json_acct_files = []
    json_path = str(speckle_path_provider.accounts_folder_path())
    try:
        os.makedirs(json_path, exist_ok=True)
        json_acct_files.extend(
            file for file in os.listdir(json_path) if file.endswith(".json")
        )

    except Exception:
        # cannot find or get the json account paths
        pass

    if json_acct_files:
        try:
            accounts.extend(
                Account.model_validate_json(Path(json_path, json_file).read_text())
                # Account.parse_file(os.path.join(json_path, json_file))
                for json_file in json_acct_files
            )
        except Exception as ex:
            raise SpeckleException(
                "Invalid json accounts could not be read. Please fix or remove them.",
                ex,
            ) from ex

    return accounts


def get_default_account(base_path: Optional[str] = None) -> Optional[Account]:
    """
    Gets this environment's default account if any. If there is no default,
    the first found will be returned and set as default.
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
    # metrics.initialise_tracker(default)

    return default


def get_account_from_token(token: str, server_url: str = None) -> Account:
    """Gets the local account for the token if it exists
    Arguments:
        token {str} -- the api token

    Returns:
        Account -- the local account with this token or a shell account containing
        just the token and url if no local account is found
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


def get_accounts_for_server(host: str) -> List[Account]:
    all_accounts = get_local_accounts()
    filtered: List[Account] = []

    for acc in all_accounts:
        moved_from = (
            acc.serverInfo.migration.movedFrom if acc.serverInfo.migration else None
        )

        if moved_from and host == urlparse(moved_from).netloc:
            filtered.append(acc)

    for acc in all_accounts:
        if any([x for x in filtered if x.userInfo.id == acc.userInfo.id]):
            continue

        if host == urlparse(acc.serverInfo.url).netloc:
            filtered.append(acc)

    return filtered


class StreamWrapper:
    def __init__(self, url: str = None) -> None:
        raise SpeckleException(
            message=(
                "The StreamWrapper has moved as of v2.6.0! Please import from"
                " specklepy.api.wrapper"
            ),
            exception=DeprecationWarning(),
        )
