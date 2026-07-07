from typing import Any, Tuple

from gql.client import Client

from specklepy.api.credentials import Account
from specklepy.core.api.resource import ResourceBase as CoreResourceBase


class ResourceBase(CoreResourceBase):
    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        name: str,
        server_version: Tuple[Any, ...] | None = None,
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=name,
            server_version=server_version,
        )
