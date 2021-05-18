from typing import Dict, List
from gql import gql
from gql.client import Client
from specklepy.api.models import ServerInfo
from specklepy.api.resource import ResourceBase


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
                    version
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
            query Apps {
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

    def create_token(self, name: str, scopes: List[str], lifespan: int) -> str:
        """Create a personal API token

        Arguments:
            scopes {List[str]} -- the scopes to grant with this token
            name {str} -- a name for your new token
            lifespan {int} -- duration before the token expires

        Returns:
            str -- the new API token. note: this is the only time you'll see the token!
        """
        query = gql(
            """
            mutation TokenCreate($token: ApiTokenCreateInput!) {
                apiTokenCreate(token: $token)
            }
            """
        )
        params = {"token": {"scopes": scopes, "name": name, "lifespan": lifespan}}

        return self.make_request(
            query=query,
            params=params,
            return_type="apiTokenCreate",
            parse_response=False,
        )

    def revoke_token(self, token: str) -> bool:
        """Revokes (deletes) a personal API token

        Arguments:
            token {str} -- the token to revoke (delete)

        Returns:
            bool -- True if the token was successfully deleted
        """
        query = gql(
            """
            mutation TokenRevoke($token: String!) {
                apiTokenRevoke(token: $token)
            }
            """
        )
        params = {"token": token}

        return self.make_request(
            query=query,
            params=params,
            return_type="apiTokenRevoke",
            parse_response=False,
        )
