from typing import Any, Dict, List, Tuple

from specklepy.api.models import ServerInfo
from specklepy.core.api.resources import ServerResource as CoreResource
from specklepy.logging import metrics


class ServerResource(CoreResource):
    """API Access class for the server"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
        )

    def get(self) -> ServerInfo:
        """Get the server info

        Returns:
            dict -- the server info in dictionary form
        """
        metrics.track(metrics.SDK, self.account, {"name": "Server Get"})
        return super().get()

    def version(self) -> Tuple[Any, ...]:
        """Get the server version

        Returns:
            the server version in the format (major, minor, patch, (tag, build))
            eg (2, 6, 3) for a stable build and (2, 6, 4, 'alpha', 4711) for alpha
        """
        # not tracking as it will be called along with other mutations / queries as a check
        return super().version()

    def apps(self) -> Dict:
        """Get the apps registered on the server

        Returns:
            dict -- a dictionary of apps registered on the server
        """
        metrics.track(metrics.SDK, self.account, {"name": "Server Apps"})
        return super().apps()

    def create_token(self, name: str, scopes: List[str], lifespan: int) -> str:
        """Create a personal API token

        Arguments:
            scopes {List[str]} -- the scopes to grant with this token
            name {str} -- a name for your new token
            lifespan {int} -- duration before the token expires

        Returns:
            str -- the new API token. note: this is the only time you'll see the token!
        """
        metrics.track(metrics.SDK, self.account, {"name": "Server Create Token"})
        return super().create_token(name, scopes, lifespan)

    def revoke_token(self, token: str) -> bool:
        """Revokes (deletes) a personal API token

        Arguments:
            token {str} -- the token to revoke (delete)

        Returns:
            bool -- True if the token was successfully deleted
        """
        metrics.track(metrics.SDK, self.account, {"name": "Server Revoke Token"})
        return super().revoke_token(token)
