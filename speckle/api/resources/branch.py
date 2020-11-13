from typing import List, Optional
from gql import gql
from pydantic.main import BaseModel
from speckle.api.resource import ResourceBase
from speckle.api.resources.user import User
from speckle.api.resources.commit import CommitCollection

NAME = "branch"
METHODS = ["create"]


class Branch(BaseModel):
    id: str
    name: str
    author: Optional[User]
    description: Optional[str]
    commits: CommitCollection


class BranchCollection(BaseModel):
    totalCount: int
    cursor: Optional[str]
    items: List[Branch] = []


class Resource(ResourceBase):
    """API Access class for branches"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )

    def create(self, name: str, description: str = "No description provided") -> str:
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
                "streamId": self.id,
                "name": name,
                "description": description,
            }
        }

        return self.make_request(query=query, params=params, parse_response=False)
