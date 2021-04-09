from typing import Optional, List
from gql import gql
from pydantic.main import BaseModel
from specklepy.api.resource import ResourceBase
from specklepy.api.models import Commit


NAME = "commit"
METHODS = []


class Resource(ResourceBase):
    """API Access class for commits"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )
        self.schema = Commit

    def get(self, stream_id: str, commit_id: str) -> Commit:
        """
        Gets a commit given a stream and the commit id

        Arguments:
            stream_id {str} -- the stream where we can find the commit
            commit_id {str} -- the id of the commit you want to get

        Returns:
            Commit -- the retrieved commit object
        """
        query = gql(
            """
            query Commit($stream_id: String!, $commit_id: String!) {
                stream(id: $stream_id) {
                    commit(id: $commit_id) {
                        id
                        referencedObject
                        message
                        authorId
                        authorName
                        authorAvatar
                        createdAt
                        sourceApplication
                        totalChildrenCount
                        parents
                    }
                }
            }
            """
        )
        params = {"stream_id": stream_id, "commit_id": commit_id}

        return self.make_request(
            query=query, params=params, return_type=["stream", "commit"]
        )

    def list(self, stream_id: str, limit: int = 10) -> List[Commit]:
        """
        Get a list of commits on a given stream

        Arguments:
            stream_id {str} -- the stream where the commits are
            limit {int} -- the maximum number of commits to fetch (default = 10)

        Returns:
            List[Commit] -- a list of the most recent commit objects
        """
        query = gql(
            """
            query Commits($stream_id: String!, $limit: Int!) {
                stream(id: $stream_id) {
                    commits(limit: $limit) {
                        items {
                            id
                            message
                            referencedObject
                            authorName
                            authorId
                            authorName
                            authorAvatar
                            createdAt
                            sourceApplication
                            totalChildrenCount
                            parents
                        }
                    }
                }
            }
            """
        )
        params = {"stream_id": stream_id, "limit": limit}

        return self.make_request(
            query=query, params=params, return_type=["stream", "commits", "items"]
        )

    def create(
        self,
        stream_id: str,
        object_id: str,
        branch_name: str = "main",
        message: str = "",
        source_application: str = "python",
        parents: List[str] = None,
    ) -> str:
        """
        Creates a commit on a branch

        Arguments:
            stream_id {str} -- the stream you want to commit to
            object_id {str} -- the hash of your commit object
            branch_name {str} -- the name of the branch to commit to (defaults to "main")
            message {str} -- optional: a message to give more information about the commit
            source_application{str} -- optional: the application from which the commit was created (defaults to "python")
            parents {List[str]} -- optional: the id of the parent commits

        Returns:
            str -- the id of the created commit
        """
        query = gql(
            """
            mutation CommitCreate ($commit: CommitCreateInput!){ commitCreate(commit: $commit)}
            """
        )
        params = {
            "commit": {
                "streamId": stream_id,
                "branchName": branch_name,
                "objectId": object_id,
                "message": message,
                "sourceApplication": source_application,
            }
        }
        if parents:
            params["commit"]["parents"] = parents

        return self.make_request(
            query=query, params=params, return_type="commitCreate", parse_response=False
        )

    def update(self, stream_id: str, commit_id: str, message: str) -> bool:
        """
        Update a commit

        Arguments:
            stream_id {str} -- the id of the stream that contains the commit you'd like to update
            commit_id {str} -- the id of the commit you'd like to update
            message {str} -- the updated commit message

        Returns:
            bool -- True if the operation succeeded
        """
        query = gql(
            """
            mutation CommitUpdate($commit: CommitUpdateInput!){ commitUpdate(commit: $commit)}
            """
        )
        params = {
            "commit": {"streamId": stream_id, "id": commit_id, "message": message}
        }

        return self.make_request(
            query=query, params=params, return_type="commitUpdate", parse_response=False
        )

    def delete(self, stream_id: str, commit_id: str) -> bool:
        """
        Delete a commit

        Arguments:
            stream_id {str} -- the id of the stream that contains the commit you'd like to delete
            commit_id {str} -- the id of the commit you'd like to delete

        Returns:
            bool -- True if the operation succeeded
        """
        query = gql(
            """
            mutation CommitDelete($commit: CommitDeleteInput!){ commitDelete(commit: $commit)}
            """
        )
        params = {"commit": {"streamId": stream_id, "id": commit_id}}

        return self.make_request(
            query=query, params=params, return_type="commitDelete", parse_response=False
        )
