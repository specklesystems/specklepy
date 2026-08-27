from threading import Lock
from typing import Any, Tuple, Type, TypeVar

from gql import GraphQLRequest
from gql.client import Client
from gql.transport.exceptions import TransportQueryError
from pydantic import BaseModel

from specklepy.api.credentials import Account
from specklepy.logging.exceptions import (
    GraphQLException,
    SpeckleException,
    UnsupportedException,
)

T = TypeVar("T", bound=BaseModel)


class ResourceBase:
    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        name: str,
        server_version: Tuple[Any, ...] | None = None,
    ) -> None:
        self.account = account
        self.basepath = basepath
        self.client = client
        self.name = name
        self.server_version = server_version
        self.__lock = Lock()

    def make_request_and_parse_response(
        self,
        schema: Type[T],
        request: GraphQLRequest,
    ) -> T:
        try:
            with self.__lock:
                response = self.client.execute(request)
        except TransportQueryError as ex:
            raise GraphQLException(
                message=(
                    f"Failed to execute the GraphQL {self.name} request. Errors:"
                    f" {ex.errors}"
                ),
                errors=ex.errors,
                data=ex.data,
            ) from ex
        except Exception as ex:
            raise SpeckleException(
                message=(
                    f"Failed to execute the GraphQL {self.name} request. Inner"
                    f" exception: {ex}"
                ),
                exception=ex,
            ) from ex

        return schema.model_validate(response)

    def _check_server_version_at_least(
        self, target_version: Tuple[Any, ...], unsupported_message: str | None = None
    ):
        """Use this check to guard against making unsupported requests on older servers.

        Arguments:
            target_version {tuple}
            the minimum server version in the format (major, minor, patch, (tag, build))
            eg (2, 6, 3) for a stable build and (2, 6, 4, 'alpha', 4711) for alpha
        """
        if not unsupported_message:
            unsupported_message = (
                "The client method used is not supported on Speckle Server versions"
                f" prior to v{'.'.join(target_version)}"
            )
        # if version is dev, it should be supported... (or not)
        if self.server_version == ("dev",):
            return
        if self.server_version and self.server_version < target_version:
            raise UnsupportedException(unsupported_message)

    def _check_invites_supported(self):
        """Invites are only supported for Speckle Server >= 2.6.4.
        Use this check to guard against making unsupported requests on older servers.
        """
        self._check_server_version_at_least(
            (2, 6, 4),
            "Stream invites are only supported as of Speckle Server v2.6.4. Please"
            " update your Speckle Server to use this method or use the"
            " `grant_permission` flow instead.",
        )
