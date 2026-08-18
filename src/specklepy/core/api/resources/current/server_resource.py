import re
from typing import Any, Dict, List, Tuple

from gql import gql

from specklepy.core.api.models import ServerInfo
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

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
        request = gql(
            """
            query Server {
                data:serverInfo {
                    name
                    company
                    description
                    adminContact
                    canonicalUrl
                    version
                    scopes {
                        name
                        description
                    }
                    authStrategies{
                        id
                        name
                        icon
                    }
                    workspaces {
                      workspacesEnabled
                    }
                }
            }
            """
        )

        return self.make_request_and_parse_response(
            DataResponse[ServerInfo], request
        ).data

    def version(self) -> Tuple[Any, ...]:
        """Get the server version

        Returns:
            the server version in the format (major, minor, patch, (tag, build))
            eg (2, 6, 3) for a stable build and (2, 6, 4, 'alpha', 4711) for alpha
        """
        # not tracking as it will be called along with other mutations / queries
        # as a check
        request = gql(
            """
            query Server {
                data:serverInfo {
                    data:version
                }
            }
            """
        )
        ver = self.make_request_and_parse_response(
            DataResponse[DataResponse[str]], request
        ).data.data

        # pylint: disable=consider-using-generator; (list comp is faster)
        return tuple(
            [
                int(segment) if segment.isdigit() else segment
                for segment in re.split(r"\.|-", ver)
            ]
        )

    def apps(self) -> List[Dict[str, Any]]:
        """Get the apps registered on the server

        Returns:
            a list of apps registered on the server, in dictionary form
        """
        request = gql(
            """
            query Apps {
                data:apps{
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

        return self.make_request_and_parse_response(
            DataResponse[List[Dict[str, Any]]], request
        ).data

    def create_token(self, name: str, scopes: List[str], lifespan: int) -> str:
        """Create a personal API token

        Arguments:
            scopes {List[str]} -- the scopes to grant with this token
            name {str} -- a name for your new token
            lifespan {int} -- duration before the token expires

        Returns:
            str -- the new API token. note: this is the only time you'll see the token!
        """
        request = gql(
            """
            mutation TokenCreate($token: ApiTokenCreateInput!) {
                data:apiTokenCreate(token: $token)
            }
            """
        )
        request.variable_values = {
            "token": {"scopes": scopes, "name": name, "lifespan": lifespan}
        }

        return self.make_request_and_parse_response(DataResponse[str], request).data

    def revoke_token(self, token: str) -> bool:
        """Revokes (deletes) a personal API token

        Arguments:
            token {str} -- the token to revoke (delete)

        Returns:
            bool -- True if the token was successfully deleted
        """
        request = gql(
            """
            mutation TokenRevoke($token: String!) {
                data:apiTokenRevoke(token: $token)
            }
            """
        )
        request.variable_values = {"token": token}

        return self.make_request_and_parse_response(DataResponse[bool], request).data
