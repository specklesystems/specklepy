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


class ResourceBase(object):
    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        name: str,
        server_version: Optional[Tuple[Any, ...]] = None,
    ) -> None:
        self.account = account
        self.basepath = basepath
        self.client = client
        self.name = name
        self.server_version = server_version
        self.schema: Optional[Type] = None

    def _step_into_response(self, response: dict, return_type: Union[str, List, None]):
        """Step into the dict to get the relevant data"""
        if return_type is None:
            return response
        if isinstance(return_type, str):
            return response[return_type]
        if isinstance(return_type, List):
            for key in return_type:
                response = response[key]
            return response

    def _parse_response(self, response: Union[dict, list, None], schema=None):
        """Try to create a class instance from the response"""
        if response is None:
            return None
        if isinstance(response, list):
            return [self._parse_response(response=r, schema=schema) for r in response]
        if schema:
            return schema.parse_obj(response)
        elif self.schema:
            try:
                return self.schema.parse_obj(response)
            except Exception:
                s = BaseObjectSerializer(read_transport=SQLiteTransport())
                return s.recompose_base(response)
        else:
            return response

    def make_request(
        self,
        query: DocumentNode,
        params: Optional[Dict] = None,
        return_type: Union[str, List, None] = None,
        schema=None,
        parse_response: bool = True,
    ) -> Any:
        """Executes the GraphQL query"""
        try:
            response = self.client.execute(query, variable_values=params)
        except Exception as ex:
            if isinstance(ex, TransportQueryError):
                return GraphQLException(
                    message=(
                        f"Failed to execute the GraphQL {self.name} request. Errors:"
                        f" {ex.errors}"
                    ),
                    errors=ex.errors,
                    data=ex.data,
                )
            else:
                return SpeckleException(
                    message=(
                        f"Failed to execute the GraphQL {self.name} request. Inner"
                        f" exception: {ex}"
                    ),
                    exception=ex,
                )

        response = self._step_into_response(response=response, return_type=return_type)

        if parse_response:
            return self._parse_response(response=response, schema=schema)
        else:
            return response

    def _check_server_version_at_least(
        self, target_version: Tuple[Any, ...], unsupported_message: Optional[str] = None
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
