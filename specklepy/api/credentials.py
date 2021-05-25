from typing import List, Optional
from pydantic import BaseModel
from specklepy.api.models import ServerInfo
from specklepy.transports.sqlite import SQLiteTransport

account_storage = SQLiteTransport(scope="Accounts")


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


def get_local_accounts() -> List[Account]:
    """Gets all the accounts present in this environment

    Returns:
        List[Account] -- list of all local accounts or an empty list if no accounts were found
    """
    res = account_storage.get_all_objects()
    return [Account.parse_raw(r[1]) for r in res] if res else []


def get_default_account() -> Account:
    """Gets this environment's default account if any. If there is no default, the first found will be returned and set as default.

    Returns:
        Account -- the default account or None if no local accounts were found
    """
    accounts = get_local_accounts()
    if not accounts:
        return None

    default = next((acc for acc in accounts if acc.isDefault), None)
    if not default:
        default = accounts[0]
        default.isDefault = True

    return default
