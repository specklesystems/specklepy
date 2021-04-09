from specklepy.logging.exceptions import SpeckleException
from typing import List, Optional
from gql import gql
from pydantic.main import BaseModel
from specklepy.api.resource import ResourceBase
from specklepy.api.models import User

NAME = "user"
METHODS = ["get"]


class Resource(ResourceBase):
    """API Access class for users"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )
        self.schema = User

    def get(self, id: str = None) -> User:
        """Gets the profile of a user. If no id argument is provided, will return the current authenticated user's profile (as extracted from the authorization header).

        Arguments:
            id {str} -- the user id

        Returns:
            User -- the retrieved user
        """
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
