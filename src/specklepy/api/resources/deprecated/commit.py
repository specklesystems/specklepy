from typing import List, Optional, Union

from deprecated import deprecated

from specklepy.api.models import Commit
from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resources.deprecated.commit import Resource as CoreResource
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException


class Resource(CoreResource):
    """API Access class for commits"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
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
        metrics.track(metrics.SDK, self.account, {"name": "Commit Get"})
        return super().get(stream_id, commit_id)

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
        metrics.track(metrics.SDK, self.account, {"name": "Commit List"})
        return super().list(stream_id, limit)

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
        metrics.track(metrics.SDK, self.account, {"name": "Commit Create"})
        return super().create(
            stream_id, object_id, branch_name, message, source_application, parents
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
        metrics.track(metrics.SDK, self.account, {"name": "Commit Update"})
        return super().update(stream_id, commit_id, message)

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
        metrics.track(metrics.SDK, self.account, {"name": "Commit Delete"})
        return super().delete(stream_id, commit_id)

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
        metrics.track(metrics.SDK, self.account, {"name": "Commit Received"})
        return super().received(stream_id, commit_id, source_application, message)
