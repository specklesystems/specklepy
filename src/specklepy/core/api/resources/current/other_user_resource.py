from datetime import datetime, timezone
from typing import List, Optional, Union

from deprecated import deprecated
from gql import gql

from specklepy.core.api.models import (
    ActivityCollection,
    LimitedUser,
    UserSearchResultCollection,
)
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import SpeckleException

NAME = "other_user"


class OtherUserResource(ResourceBase):
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

    def get(self, id: str) -> Optional[LimitedUser]:
        """
        Gets the profile of another user.

        Arguments:
            id {str} -- the user id

        Returns:
            LimitedUser -- the retrieved profile of another user
        """
        QUERY = gql(
            """
          query LimitedUser($id: String!) {
            data:otherUser(id: $id){
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

        variables = {"id": id}

        return self.make_request_and_parse_response(
            DataResponse[Optional[LimitedUser]], QUERY, variables
        ).data

    def user_search(
        self,
        query: str,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        archived: bool = False,
        emailOnly: bool = False,
    ) -> UserSearchResultCollection:
        """Searches for a user on the server, by name or email. The search query must be at least
        3 characters long

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
            cursor {Optional[str]} --
            archived {bool} --
            emailOnly {bool} --
        Returns:
            ResourceCollection[LimitedUser] -- User objects that match the search query
        """

        QUERY = gql(
            """
            query UserSearch($query: String!, $limit: Int!, $cursor: String, $archived: Boolean, $emailOnly: Boolean) {
              data:userSearch(query: $query, limit: $limit, cursor: $cursor, archived: $archived, emailOnly: $emailOnly) {
                cursor
                items {
                 id
                 name
                 bio
                 company
                 avatar
                 verified
                 role
               }
             }
            }
            """
        )
        variables = {
            "query": query,
            "limit": limit,
            "cursor": cursor,
            "archived": archived,
            "emailOnly": emailOnly,
        }

        return self.make_request_and_parse_response(
            DataResponse[UserSearchResultCollection], QUERY, variables
        ).data

    @deprecated(reason="Use user_search instead", version=FE1_DEPRECATION_VERSION)
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
                      role
                    }
                }
            }
          """
        )
        params = {"search_query": search_query, "limit": limit}

        return self.make_request(
            query=query, params=params, return_type=["userSearch", "items"]
        )

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
