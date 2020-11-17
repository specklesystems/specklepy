from typing import List, Optional
from gql import gql
from pydantic.main import BaseModel
from speckle.api.resource import ResourceBase
from speckle.api.models import Branch

NAME = "branch"
METHODS = ["create"]


class Resource(ResourceBase):
    """API Access class for branches"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )
        self.schema = Branch

    def create(
        self, streamId: str, name: str, description: str = "No description provided"
    ) -> str:
        """Create a new branch on this stream

        Arguments:
            name {str} -- the name of the new branch
            description {str} -- a short description of the branch

        Returns:
            id {str} -- the newly created branch's id
        """

        query = gql(
            """
            mutation BranchCreate($branch: BranchCreateInput!){
              branchCreate(branch: $branch)
            }
          """
        )
        params = {
            "branch": {
                "streamId": streamId,
                "name": name,
                "description": description,
            }
        }

        return self.make_request(query=query, params=params, parse_response=False)
