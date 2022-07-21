from graphql import DocumentNode
from specklepy.api.credentials import Account
from specklepy.transports.sqlite import SQLiteTransport
from typing import Any, Dict, List, Type, Union
from gql.client import Client
from gql.transport.exceptions import TransportQueryError
from specklepy.logging.exceptions import GraphQLException, SpeckleException
from specklepy.serialization.base_object_serializer import BaseObjectSerializer


class ResourceBase(object):
    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        name: str,
    ) -> None:
        self.account = account
        self.basepath = basepath
        self.client = client
        self.name = name
        self.schema: Union[Type, None] = None

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

    def _parse_response(self, response: Union[dict, list], schema=None):
        """Try to create a class instance from the response"""
        if isinstance(response, list):
            return [self._parse_response(response=r, schema=schema) for r in response]
        if schema:
            return schema.parse_obj(response)
        elif self.schema:
            try:
                return self.schema.parse_obj(response)
            except:
                s = BaseObjectSerializer(read_transport=SQLiteTransport())
                return s.recompose_base(response)
        else:
            return response

    def make_request(
        self,
        query: DocumentNode,
        params: Dict = None,
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
                    message=f"Failed to execute the GraphQL {self.name} request. Errors: {ex.errors}",
                    errors=ex.errors,
                    data=ex.data,
                )
            else:
                return SpeckleException(
                    message=f"Failed to execute the GraphQL {self.name} request. Inner exception: {ex}",
                    exception=ex,
                )

        response = self._step_into_response(response=response, return_type=return_type)

        if parse_response:
            return self._parse_response(response=response, schema=schema)
        else:
            return response
