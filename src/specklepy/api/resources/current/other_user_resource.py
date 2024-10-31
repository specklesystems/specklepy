from datetime import datetime
from typing import List, Optional, Union

from deprecated import deprecated

from specklepy.core.api.models import (
    ActivityCollection,
    LimitedUser,
    UserSearchResultCollection,
)
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resources import OtherUserResource as CoreResource
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException


class OtherUserResource(CoreResource):
    """
    Provides API access to other users' profiles and activities on the platform.
    This class enables fetching limited information about users, searching for users by name or email,
    and accessing user activity logs with appropriate privacy and access control measures in place.
    """

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=(server_version,),
        )
        self.schema = LimitedUser

    def get(self, id: str) -> Optional[LimitedUser]:
        metrics.track(metrics.SDK, self.account, {"name": "Other User Get"})
        return super().get(id)

    def user_search(
        self,
        query: str,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        archived: bool = False,
        emailOnly: bool = False,
    ) -> UserSearchResultCollection:
        metrics.track(metrics.SDK, self.account, {"name": "Other User Search"})
        return super().user_search(
            query, limit=limit, cursor=cursor, archived=archived, emailOnly=emailOnly
        )

    @deprecated(reason="Use user_search instead", version=FE1_DEPRECATION_VERSION)
    def search(
        self, search_query: str, limit: int = 25
    ) -> Union[List[LimitedUser], SpeckleException]:
        """
        Searches for users by name or email.
        The search requires a minimum query length of 3 characters.

        Args:
            search_query (str): The search string.
            limit (int): Maximum number of search results to return.

        Returns:
            Union[List[LimitedUser], SpeckleException]: A list of users matching the search
                query or an exception if the query is too short.
        """
        if len(search_query) < 3:
            return SpeckleException(
                message="User search query must be at least 3 characters."
            )

        metrics.track(metrics.SDK, self.account, {"name": "Other User Search"})
        return super().search(search_query, limit)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def activity(
        self,
        user_id: str,
        limit: int = 20,
        action_type: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        cursor: Optional[datetime] = None,
    ) -> ActivityCollection:
        """
        Retrieves a collection of activities for a specified user, with optional filters for activity type,
        time frame, and pagination.

        Args:
            user_id (str): The ID of the user whose activities are being requested.
            limit (int): The maximum number of activity items to return.
            action_type (Optional[str]): A specific type of activity to filter.
            before (Optional[datetime]): Latest timestamp to include activities before.
            after (Optional[datetime]): Earliest timestamp to include activities after.
            cursor (Optional[datetime]): Timestamp for pagination cursor.

        Returns:
            ActivityCollection: A collection of user activities filtered according to specified criteria.
        """
        metrics.track(metrics.SDK, self.account, {"name": "Other User Activity"})
        return super().activity(user_id, limit, action_type, before, after, cursor)
