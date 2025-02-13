from typing import Optional

from specklepy.core.api.models import (
    LimitedUser,
    UserSearchResultCollection,
)
from specklepy.core.api.resources import OtherUserResource as CoreResource
from specklepy.logging import metrics


class OtherUserResource(CoreResource):
    """
    Provides API access to other users' profiles and activities on the platform.
    This class enables fetching limited information about users,
    searching for users by name or email,
    and accessing user activity logs with appropriate privacy
    and access control measures in place.
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
