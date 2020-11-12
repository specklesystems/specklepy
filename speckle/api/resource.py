from speckle.logging.exceptions import GraphQLException
from typing import Dict, List
from gql.client import Client
from gql.gql import gql
from gql.transport.exceptions import TransportQueryError


class ResourceBase(object):
    def __init__(
        self,
        me: Dict,
        basepath: str,
        client: Client,
        name: str,
        methods: list,
    ) -> None:
        self.me = me
        self.basepath = basepath
        self.client = client
        self.name = name
        self.methods = methods
        self.schema = None

    def _parse_response(self, response: dict or list, schema=None):
        if isinstance(response, list):
            return [self._parse_response(response=r, schema=schema) for r in response]
        if schema:
            return schema.parse_obj(response)
        elif self.schema:
            return self.schema.parse_obj(response)
        else:
            return response

    def make_request(
        self,
        query: gql,
        params: Dict = None,
        return_type: str or List = None,
        schema=None,
        parse_response: bool = True,
    ) -> Dict or GraphQLException:
        """Executes the GraphQL query"""
        try:
            response = self.client.execute(query, variable_values=params)
        except TransportQueryError as e:
            return GraphQLException(
                message=f"Failed to execute the GraphQL {self.name} request. Errors: {e.errors}",
                errors=e.errors,
                data=e.data,
            )

        if isinstance(return_type, str):
            response = response[return_type]
        elif isinstance(return_type, List):
            for key in return_type:
                response = response[key]

        if parse_response:
            return self._parse_response(response=response, schema=schema)
        else:
            return response
