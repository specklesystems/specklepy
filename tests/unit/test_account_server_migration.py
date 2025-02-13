import os
import uuid
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import pytest

from specklepy.core.api.credentials import Account, UserInfo, get_accounts_for_server
from specklepy.core.api.models import ServerInfo, ServerMigration
from specklepy.core.helpers import speckle_path_provider


def _create_account(
    id: str, url: str, movedFrom: Optional[str], movedTo: Optional[str]
) -> Account:
    return Account(
        id=uuid.uuid4().hex[:6].lower(),
        token="myToken",
        serverInfo=ServerInfo(
            url=url,
            name="myServer",
            migration=ServerMigration(moved_to=movedTo, moved_from=movedFrom),
        ),
        userInfo=UserInfo(id=id),
    )


def _test_cases() -> List[Tuple[List[Account], str, List[Account]]]:
    user_id_1 = uuid.uuid4().hex[:6].lower()
    user_id_2 = uuid.uuid4().hex[:6].lower()
    old = _create_account(
        user_id_1, "https://old.example.com", None, "https://new.example.com"
    )
    new = _create_account(
        user_id_1, "https://new.example.com", "https://old.example.com", None
    )
    other = _create_account(user_id_2, "https://other.example.com", None, None)

    given_accounts = [old, new, other]
    reversed = [other, new, old]

    return [
        (given_accounts, "https://old.example.com", [new]),
        (given_accounts, "https://new.example.com", [new]),
        (reversed, "https://old.example.com", [new]),
    ]


def _clean_accounts(accounts: List[Account]) -> None:
    json_accounts = speckle_path_provider.accounts_folder_path()

    for acc in accounts:
        # deleting acc json file in json_accounts path
        os.remove(os.path.join(json_accounts, f"{acc.id}.json"))
        pass


def _add_accounts(accounts: List[Account]) -> None:
    json_accounts = speckle_path_provider.accounts_folder_path()

    for acc in accounts:
        data = Account.model_dump_json(acc)
        with open(os.path.join(json_accounts, f"{acc.id}.json"), "w") as f:
            f.write(data)


@pytest.mark.parametrize("accounts, requested_url, expected", _test_cases())
def test_server_migration(
    accounts: List[Account], requested_url: str, expected: List[Account]
) -> None:
    _add_accounts(accounts)
    try:
        res = get_accounts_for_server(urlparse(requested_url).netloc)
        assert res == expected

    finally:
        _clean_accounts(accounts)
