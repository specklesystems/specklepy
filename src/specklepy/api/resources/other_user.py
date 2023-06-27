from datetime import datetime, timezone
from typing import List, Optional, Union

from gql import gql

from specklepy.api.models import ActivityCollection, LimitedUser
from specklepy.api.resource import ResourceBase
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException

from specklepy.core.api.resources.other_user import NAME, Resource as Core_Resource


class Resource(Core_Resource):
    """API Access class for other users, that are not the currently active user."""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )
        self.schema = LimitedUser

    def get(self, id: str) -> LimitedUser:
        """
        Gets the profile of another user.

        Arguments:
            id {str} -- the user id

        Returns:
            LimitedUser -- the retrieved profile of another user
        """
        metrics.track(metrics.SDK, self.account, {"name": "Other User Get"})
        
        return super().get(id)

    def search(
        self, search_query: str, limit: int = 25
    ) -> Union[List[LimitedUser], SpeckleException]:
        """Searches for user by name or email. The search query must be at least
        3 characters long

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
        Returns:
            List[LimitedUser] -- a list of User objects that match the search query
        """
        if len(search_query) < 3:
            return SpeckleException(
                message="User search query must be at least 3 characters"
            )

        metrics.track(metrics.SDK, self.account, {"name": "Other User Search"})
        
        return super().search(search_query, limit) 

