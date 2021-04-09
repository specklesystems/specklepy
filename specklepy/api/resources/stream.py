from typing import Dict, List, Optional
from gql import gql
from specklepy.api.resource import ResourceBase
from specklepy.api.models import Stream

NAME = "stream"
METHODS = [
    "list",
    "create",
    "get",
    "update",
    "delete",
    "search",
]


class Resource(ResourceBase):
    """API Access class for streams"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )

        self.schema = Stream

    def get(self, id: str, branch_limit: int = 10, commit_limit: int = 10) -> Stream:
        """Get the specified stream from the server

        Arguments:
            id {str} -- the stream id
            branch_limit {int} -- the maximum number of branches to return
            commit_limit {int} -- the maximum number of commits to return

        Returns:
            Stream -- the retrieved stream
        """
        query = gql(
            """
            query Stream($id: String!, $branch_limit: Int!, $commit_limit: Int!) {
              stream(id: $id) {
                id
                name
                description
                isPublic
                createdAt
                updatedAt
                collaborators {
                  id
                  name
                  role
                  avatar
                }
                branches(limit: $branch_limit) {
                  totalCount
                  cursor
                  items {
                    id
                    name
                    description
                    commits(limit: $commit_limit) {
                      totalCount
                      cursor
                      items {
                        id
                        referencedObject
                        message
                        authorName
                        authorId
                        createdAt
                      }
                    }
                  }
                }
              }
            }
          """
        )

        params = {"id": id, "branch_limit": branch_limit, "commit_limit": commit_limit}

        return self.make_request(query=query, params=params, return_type="stream")

    def list(self, stream_limit: int = 10) -> List[Stream]:
        """Get a list of the user's streams

        Arguments:
            stream_limit {int} -- The maximum number of streams to return

        Returns:
            List[Stream] -- A list of Stream objects
        """
        query = gql(
            """
            query User($stream_limit: Int!) {
              user {
                id
                email
                name
                bio
                company
                avatar
                verified
                profiles
                role
                streams(limit: $stream_limit) {
                  totalCount
                  cursor
                  items {
                    id
                    name
                    description
                    isPublic
                    createdAt
                    updatedAt
                    collaborators {
                      id
                      name
                      role
                    }
                  }
                }
              }
            }
          """
        )

        params = {"stream_limit": stream_limit}

        return self.make_request(
            query=query, params=params, return_type=["user", "streams", "items"]
        )

    def create(
        self,
        name: str = "Anonymous Python Stream",
        description: str = "No description provided",
        is_public: bool = True,
    ) -> str:
        """Create a new stream

        Arguments:
            name {str} -- the name of the string
            description {str} -- a short description of the stream
            is_public {bool} -- whether or not the stream can be viewed by anyone with the id

        Returns:
            id {str} -- the id of the newly created stream
        """
        query = gql(
            """
            mutation StreamCreate($stream: StreamCreateInput!) {
              streamCreate(stream: $stream)
            }
        """
        )

        params = {
            "stream": {"name": name, "description": description, "isPublic": is_public}
        }

        return self.make_request(
            query=query, params=params, return_type="streamCreate", parse_response=False
        )

    def update(
        self, id: str, name: str = None, description: str = None, is_public: bool = None
    ) -> bool:
        """Update an existing stream

        Arguments:
            id {str} -- the id of the stream to be updated
            name {str} -- the name of the string
            description {str} -- a short description of the stream
            is_public {bool} -- whether or not the stream can be viewed by anyone with the id

        Returns:
            bool -- whether the stream update was successful
        """
        query = gql(
            """
            mutation StreamUpdate($stream: StreamUpdateInput!) {
              streamUpdate(stream: $stream)
            }
        """
        )

        params = {
            "id": id,
            "name": name,
            "description": description,
            "isPublic": is_public,
        }
        # remove None values so graphql doesn't cry
        params = {"stream": {k: v for k, v in params.items() if v is not None}}

        return self.make_request(
            query=query, params=params, return_type="streamUpdate", parse_response=False
        )

    def delete(self, id: str) -> bool:
        """Delete a stream given its id

        Arguments:
            id {str} -- the id of the stream to delete

        Returns:
            bool -- whether the deletion was successful
        """
        query = gql(
            """
            mutation StreamDelete($id: String!) {
              streamDelete(id: $id)
            }
        """
        )

        params = {"id": id}

        return self.make_request(
            query=query, params=params, return_type="streamDelete", parse_response=False
        )

    def search(
        self,
        search_query: str,
        limit: int = 25,
        branch_limit: int = 10,
        commit_limit: int = 10,
    ):
        """Search for streams by name, description, or id

        Arguments:
            search_query {str} -- a string to search for
            limit {int} -- the maximum number of results to return
            branch_limit {int} -- the maximum number of branches to return
            commit_limit {int} -- the maximum number of commits to return

        Returns:
            List[Stream] -- a list of Streams that match the search query
        """
        query = gql(
            """
            query StreamSearch($search_query: String!,$limit: Int!, $branch_limit:Int!, $commit_limit:Int!) {
              streams(query: $search_query, limit: $limit) {
                items {
                  id
                  name
                  description
                  isPublic
                  createdAt
                  updatedAt
                  collaborators {
                    id
                    name
                    role
                    avatar
                  }
                  branches(limit: $branch_limit) {
                    totalCount
                    cursor
                    items {
                      id
                      name
                      description
                      commits(limit: $commit_limit) {
                        totalCount
                        cursor
                        items {
                          id
                          referencedObject
                          message
                          authorName
                          authorId
                          createdAt
                        }
                      }
                    }
                  }
                }
              }
            }
          """
        )

        params = {
            "search_query": search_query,
            "limit": limit,
            "branch_limit": branch_limit,
            "commit_limit": commit_limit,
        }

        return self.make_request(
            query=query, params=params, return_type=["streams", "items"]
        )

    def grant_permission(self, stream_id: str, user_id: str, role: str):
        """Grant permissions to a user on a given stream

        Arguments:
            stream_id {str} -- the id of the stream to grant permissions to
            user_id {str} -- the id of the user to grant permissions for
            role {str} -- the role to grant the user

        Returns:
            bool -- True if the operation was successful
        """
        query = gql(
            """
            mutation StreamGrantPermission($permission_params: StreamGrantPermissionInput !) {
                streamGrantPermission(permissionParams: $permission_params)
            }
            """
        )

        params = {
            "permission_params": {
                "streamId": stream_id,
                "userId": user_id,
                "role": role,
            }
        }

        return self.make_request(
            query=query,
            params=params,
            return_type="streamGrantPermission",
            parse_response=False,
        )

    def revoke_permission(self, stream_id: str, user_id: str):
        """Revoke permissions from a user on a given stream

        Arguments:
            stream_id {str} -- the id of the stream to revoke permissions from
            user_id {str} -- the id of the user to revoke permissions from

        Returns:
            bool -- True if the operation was successful
        """
        query = gql(
            """
            mutation StreamRevokePermission($permission_params: StreamRevokePermissionInput !) {
                streamRevokePermission(permissionParams: $permission_params)
            }
            """
        )

        params = {"permission_params": {"streamId": stream_id, "userId": user_id}}

        return self.make_request(
            query=query,
            params=params,
            return_type="streamRevokePermission",
            parse_response=False,
        )
