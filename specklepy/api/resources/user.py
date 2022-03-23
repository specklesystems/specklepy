from datetime import datetime, timezone
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from typing import List
from gql import gql
from specklepy.api.resource import ResourceBase
from specklepy.api.models import ActivityCollection, User

NAME = "user"
METHODS = ["get", "search", "update", "activity"]


class Resource(ResourceBase):
    """API Access class for users"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            methods=METHODS,
        )
        self.schema = User

    def get(self, id: str = None) -> User:
        """Gets the profile of a user. If no id argument is provided, will return the current authenticated user's profile (as extracted from the authorization header).

        Arguments:
            id {str} -- the user id

        Returns:
            User -- the retrieved user
        """
        metrics.track(metrics.USER, self.account, {"name": "get"})
        query = gql(
            """
            query User($id: String) {
                user(id: $id) {
                    id
                    email
                    name
                    bio
                    company
                    avatar
                    verified
                    profiles
                    role
                }
            }
          """
        )

        params = {"id": id}

        return self.make_request(query=query, params=params, return_type="user")

    def search(self, search_query: str, limit: int = 25) -> List[User]:
        """Searches for user by name or email. The search query must be at least 3 characters long

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
        Returns:
            List[User] -- a list of User objects that match the search query
        """
        if len(search_query) < 3:
            return SpeckleException(
                message="User search query must be at least 3 characters"
            )

        metrics.track(metrics.USER, self.account, {"name": "search"})
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

    def update(
        self, name: str = None, company: str = None, bio: str = None, avatar: str = None
    ):
        """Updates your user profile. All arguments are optional.

        Arguments:
            name {str} -- your name
            company {str} -- the company you may or may not work for
            bio {str} -- tell us about yourself
            avatar {str} -- a nice photo of yourself

        Returns:
            bool -- True if your profile was updated successfully
        """
        metrics.track(metrics.USER, self.account, {"name": "update"})
        query = gql(
            """
            mutation UserUpdate($user: UserUpdateInput!) {
                userUpdate(user: $user)
            }
            """
        )
        params = {"name": name, "company": company, "bio": bio, "avatar": avatar}

        params = {"user": {k: v for k, v in params.items() if v is not None}}

        if not params["user"]:
            return SpeckleException(
                message="You must provide at least one field to update your user profile"
            )

        return self.make_request(
            query=query, params=params, return_type="userUpdate", parse_response=False
        )

    def activity(
        self,
        user_id: str = None,
        limit: int = 20,
        action_type: str = None,
        before: datetime = None,
        after: datetime = None,
        cursor: datetime = None,
    ):
        """
        Get the activity from a given stream in an Activity collection. Step into the activity `items` for the list of activity.
        If no id argument is provided, will return the current authenticated user's activity (as extracted from the authorization header).

        Note: all timestamps arguments should be `datetime` of any tz as they will be converted to UTC ISO format strings

        user_id {str} -- the id of the user to get the activity from
        action_type {str} -- filter results to a single action type (eg: `commit_create` or `commit_receive`)
        limit {int} -- max number of Activity items to return
        before {datetime} -- latest cutoff for activity (ie: return all activity _before_ this time)
        after {datetime} -- oldest cutoff for activity (ie: return all activity _after_ this time)
        cursor {datetime} -- timestamp cursor for pagination
        """

        query = gql(
            """
            query UserActivity($user_id: String, $action_type: String, $before:DateTime, $after: DateTime, $cursor: DateTime, $limit: Int){
                user(id: $user_id) {
                    activity(actionType: $action_type, before: $before, after: $after, cursor: $cursor, limit: $limit) {
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
            return_type=["user", "activity"],
            schema=ActivityCollection,
        )
