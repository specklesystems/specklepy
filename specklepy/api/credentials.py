import os
from typing import List, Optional
from pydantic import BaseModel
from specklepy.api.models import ServerInfo
from specklepy.transports.sqlite import SQLiteTransport
from specklepy.logging.exceptions import SpeckleException


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
