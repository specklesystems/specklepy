from datetime import datetime, timezone
from typing import List, Optional, Union

from gql import gql

from specklepy.api.models import ActivityCollection, LimitedUser
from specklepy.api.resource import ResourceBase
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException

NAME = "other_user"


class Resource(ResourceBase):
    """API Access class for other users, that are not the currently active user."""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
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
        metrics.track(metrics.OTHER_USER, self.account, {"name": "get"})
        query = gql(
            """
            query OtherUser($id: String!) {
                otherUser(id: $id) {
                    id
                    name
                    bio
                    company
                    avatar
                    verified
                    role
                }
            }
          """
        )

        params = {"id": id}

        return self.make_request(query=query, params=params, return_type="otherUser")

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

        metrics.track(metrics.OTHER_USER, self.account, {"name": "search"})
        query = gql(
            """
            query UserSearch($search_query: String!, $limit: Int!) {
                userSearch(query: $search_query, limit: $limit) {
                    items {
                        id
                        name
                        bio
                        company
                        avatar
                        verified
                    }
                }
            }
          """
        )
        params = {"search_query": search_query, "limit": limit}

        return self.make_request(
            query=query, params=params, return_type=["userSearch", "items"]
        )

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
        Get the activity from a given stream in an Activity collection.
        Step into the activity `items` for the list of activity.

        Note: all timestamps arguments should be `datetime` of
        any tz as they will be converted to UTC ISO format strings

        user_id {str} -- the id of the user to get the activity from
        action_type {str} -- filter results to a single action type
            (eg: `commit_create` or `commit_receive`)
        limit {int} -- max number of Activity items to return
        before {datetime} -- latest cutoff for activity
            (ie: return all activity _before_ this time)
        after {datetime} -- oldest cutoff for activity
            (ie: return all activity _after_ this time)
        cursor {datetime} -- timestamp cursor for pagination
        """

        query = gql(
            """
            query UserActivity(
                $user_id: String!,
                $action_type: String,
                $before:DateTime,
                $after: DateTime,
                $cursor: DateTime,
                $limit: Int
                ){
                otherUser(id: $user_id) {
                    activity(
                        actionType: $action_type,
                        before: $before,
                        after: $after,
                        cursor: $cursor,
                        limit: $limit
                        ) {
                        totalCount
                        cursor
                        items {
                            actionType
                            info
                            userId
                            streamId
                            resourceId
                            resourceType
                            message
                            time
                        }
                    }
                }
            }
            """
        )

        params = {
            "user_id": user_id,
            "limit": limit,
            "action_type": action_type,
            "before": before.astimezone(timezone.utc).isoformat() if before else before,
            "after": after.astimezone(timezone.utc).isoformat() if after else after,
            "cursor": cursor.astimezone(timezone.utc).isoformat() if cursor else cursor,
        }

        return self.make_request(
            query=query,
            params=params,
            return_type=["otherUser", "activity"],
            schema=ActivityCollection,
        )
