from typing import List, Optional, Union

from deprecated import deprecated
from gql import gql

from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
    Commit,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.logging.exceptions import SpeckleException

NAME = "commit"


class Resource(ResourceBase):
    """
    API Access class for commits
    Commit resource is deprecated, please use version resource instead
    """

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
        )
        self.schema = Commit

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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
                        message
                        referencedObject
                        authorId
                        authorName
                        authorAvatar
                        branchName
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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
                            branchName
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def create(
        self,
        stream_id: str,
        object_id: str,
        branch_name: str = "main",
        message: str = "",
        source_application: str = "python",
        parents: Optional[List[str]] = None,
    ) -> Union[str, SpeckleException]:
        """
        Creates a commit on a branch

        Arguments:
            stream_id {str} -- the stream you want to commit to
            object_id {str} -- the hash of your commit object
            branch_name {str}
                -- the name of the branch to commit to (defaults to "main")
            message {str}
                -- optional: a message to give more information about the commit
            source_application{str}
                -- optional: the application from which the commit was created
                (defaults to "python")
            parents {List[str]} -- optional: the id of the parent commits

        Returns:
            str -- the id of the created commit
        """
        query = gql(
            """
            mutation CommitCreate ($commit: CommitCreateInput!)
                { commitCreate(commit: $commit)}
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def update(self, stream_id: str, commit_id: str, message: str) -> bool:
        """
        Update a commit

        Arguments:
            stream_id {str}
                -- the id of the stream that contains the commit you'd like to update
            commit_id {str} -- the id of the commit you'd like to update
            message {str} -- the updated commit message

        Returns:
            bool -- True if the operation succeeded
        """
        query = gql(
            """
            mutation CommitUpdate($commit: CommitUpdateInput!)
                { commitUpdate(commit: $commit)}
            """
        )
        params = {
            "commit": {"streamId": stream_id, "id": commit_id, "message": message}
        }

        return self.make_request(
            query=query, params=params, return_type="commitUpdate", parse_response=False
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def delete(self, stream_id: str, commit_id: str) -> bool:
        """
        Delete a commit

        Arguments:
            stream_id {str}
                -- the id of the stream that contains the commit you'd like to delete
            commit_id {str} -- the id of the commit you'd like to delete

        Returns:
            bool -- True if the operation succeeded
        """
        query = gql(
            """
            mutation CommitDelete($commit: CommitDeleteInput!)
                { commitDelete(commit: $commit)}
            """
        )
        params = {"commit": {"streamId": stream_id, "id": commit_id}}

        return self.make_request(
            query=query, params=params, return_type="commitDelete", parse_response=False
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def received(
        self,
        stream_id: str,
        commit_id: str,
        source_application: str = "python",
        message: Optional[str] = None,
    ) -> bool:
        """
        Mark a commit object a received by the source application.
        """
        query = gql(
            """
            mutation CommitReceive($receivedInput:CommitReceivedInput!){
                commitReceive(input:$receivedInput)
            }
            """
        )
        params = {
            "receivedInput": {
                "sourceApplication": source_application,
                "streamId": stream_id,
                "commitId": commit_id,
                "message": "message",
            }
        }

        try:
            return self.make_request(
                query=query,
                params=params,
                return_type="commitReceive",
                parse_response=False,
            )
        except Exception as ex:
            print(ex.with_traceback)
            return False
