from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
from speckle.transports.sqlite import SQLiteTransport

account_storage = SQLiteTransport(scope="Accounts")


def get_local_accounts():
    res = account_storage.get_all_objects()
    return [Account.parse_raw(r[1]) for r in res] if res else []


def get_default_account():
    accounts = get_local_accounts()
    return next((acc for acc in accounts if acc.isDefault), None)


class ServerInfo(BaseModel):
    name: str
    company: Optional[str]
    url: str


class UserInfo(BaseModel):
    name: str
    email: str
    company: Optional[str]
    id: str


class Account(BaseModel):
    isDefault: bool
    token: str
    refreshToken: str
    serverInfo: ServerInfo
    userInfo: UserInfo
    id: str

    def __repr__(self) -> str:
        return f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url}, isDefault: {self.isDefault})"

    def __str__(self) -> str:
        return f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url}, isDefault: {self.isDefault})"
