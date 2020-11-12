from typing import Dict
from gql import gql
from gql.client import Client
from speckle.api.resource import ResourceBase


NAME = "server"
METHODS = ["get", "apps"]


class Resource(ResourceBase):
    """API Access class for the server"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )

    def get(self) -> Dict:
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

        return self.make_request(query=query)

    def apps(self) -> Dict:
        """Get the apps registered on the server

        Returns:
            dict -- a dictionary of apps registered on the server
        """
        query = gql(
            """
            query Apps {
              apps {
                id
                name
                description
                termsAndConditionsLink
                logo
                author {
                  id
                  name
                }
              }
            }
        """
        )

        return self.make_request(query=query)
