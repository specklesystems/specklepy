from typing import Optional

from gql import gql

from specklepy.core.api.models import (
    LimitedUser,
    UserSearchResultCollection,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

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
        """
        Searches for a user on the server, by name or email.
        The search query must be at least
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
            query UserSearch(
                $query: String!,
                $limit: Int!,
                $cursor: String,
                $archived: Boolean,
                $emailOnly: Boolean
            ) {
              data:userSearch(
                query: $query,
                limit: $limit,
                cursor: $cursor,
                archived: $archived,
                emailOnly: $emailOnly
                ) {
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
