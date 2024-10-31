import re
from typing import Any, Dict, List, Tuple

import requests
from gql import gql

from specklepy.core.api.models import ServerInfo
from specklepy.core.api.resource import ResourceBase
from specklepy.logging.exceptions import GraphQLException

NAME = "server"


class ServerResource(ResourceBase):
    """API Access class for the server"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
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

        server_info = self.make_request(
            query=query, return_type="serverInfo", schema=ServerInfo
        )
        if isinstance(server_info, ServerInfo) and isinstance(
            server_info.canonicalUrl, str
        ):
            r = requests.get(
                server_info.canonicalUrl, headers={"User-Agent": "specklepy SDK"}
            )
            if "x-speckle-frontend-2" in r.headers:
                server_info.frontend2 = True
            else:
                server_info.frontend2 = False

        return server_info

    def version(self) -> Tuple[Any, ...]:
        """Get the server version

        Returns:
            the server version in the format (major, minor, patch, (tag, build))
            eg (2, 6, 3) for a stable build and (2, 6, 4, 'alpha', 4711) for alpha
        """
        # not tracking as it will be called along with other mutations / queries as a check
        query = gql(
            """
            query Server {
                serverInfo {
                    version
                }
            }
            """
        )
        ver = self.make_request(
            query=query, return_type=["serverInfo", "version"], parse_response=False
        )
        if isinstance(ver, Exception):
            raise GraphQLException(
                f"Could not get server version for {self.basepath}", [ver]
            )

        # pylint: disable=consider-using-generator; (list comp is faster)
        return tuple(
            [
                int(segment) if segment.isdigit() else segment
                for segment in re.split(r"\.|-", ver)
            ]
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
