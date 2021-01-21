from typing import Dict
from gql import gql
from gql.client import Client
from speckle.api.models import ServerInfo
from speckle.api.resource import ResourceBase


NAME = "server"
METHODS = ["get", "apps"]


class Resource(ResourceBase):
    """API Access class for the server"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )

    def get(self) -> ServerInfo:
        """Get the server info

        Returns:
            dict -- the server info in dictionary form
        """
        query = gql(
            """
            query Server {
                serverInfo {
                    name
                    company
                    description
                    adminContact
                    canonicalUrl
                    roles {
                        name
                        description
                        resourceTarget
                    }
                    scopes {
                        name
                        description
                    }
                    authStrategies{
                        id
                        name
                        icon
                    }
                }
            }
            """
        )

        return self.make_request(
            query=query, return_type="serverInfo", schema=ServerInfo
        )

    def apps(self) -> Dict:
        """Get the apps registered on the server

        Returns:
            dict -- a dictionary of apps registered on the server
        """
        query = gql(
            """
            query {
                apps{
                    id
                    name
                    description
                    termsAndConditionsLink
                    trustByDefault
                    logo
                    author {
                        id
                        name
                        avatar
                    }
                }
            }
        """
        )

        return self.make_request(query=query, return_type="apps", parse_response=False)
