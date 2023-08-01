from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from gql.client import Client
from gql.transport.exceptions import TransportQueryError
from graphql import DocumentNode

from specklepy.api.credentials import Account
from specklepy.logging.exceptions import (
    GraphQLException,
    SpeckleException,
    UnsupportedException,
)
from specklepy.serialization.base_object_serializer import BaseObjectSerializer
from specklepy.transports.sqlite import SQLiteTransport

# following imports seem to be unnecessary, but they need to stay 
# to not break the scripts using these functions as non-core
from specklepy.core.api.resource import ResourceBase as CoreResourceBase


class ResourceBase(CoreResourceBase):
    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        name: str,
        server_version: Optional[Tuple[Any, ...]] = None,
    ) -> None:
        super().__init__(
            account = account,
            basepath = basepath,
            client = client,
            name = name,
            server_version = server_version
        )
    