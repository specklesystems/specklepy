from typing import List, Optional

# following imports seem to be unnecessary, but they need to stay
# to not break the scripts using these functions as non-core
from specklepy.core.api.credentials import StreamWrapper  # noqa: F401
from specklepy.core.api.credentials import Account, UserInfo  # noqa: F401
from specklepy.core.api.credentials import (
    get_account_from_token as core_get_account_from_token,
)
from specklepy.core.api.credentials import get_local_accounts as core_get_local_accounts
from specklepy.logging import metrics


def get_local_accounts(base_path: Optional[str] = None) -> List[Account]:
    """Gets all the accounts present in this environment

    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        List[Account] -- list of all local accounts or an empty list if
        no accounts were found
    """
    accounts = core_get_local_accounts(base_path)

    metrics.track(
        metrics.SDK,
        next(
            (acc for acc in accounts if acc.isDefault),
            accounts[0] if accounts else None,
        ),
        {"name": "Get Local Accounts"},
    )

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
    accounts = core_get_local_accounts(base_path=base_path)
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
        Account -- the local account with this token or a shell account containing
        just the token and url if no local account is found
    """
    account = core_get_account_from_token(token, server_url)

    metrics.track(metrics.SDK, account, {"name": "Get Account From Token"})
    return account
