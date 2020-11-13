from typing import Optional, List
from gql import gql
from pydantic.main import BaseModel
from speckle.api.resource import ResourceBase


NAME = "commit"
METHODS = []


class Commit(BaseModel):
    id: str
    referencedObject: str
    message: Optional[str]
    authorName: Optional[str]
    authorId: Optional[str]
    createdAt: Optional[str]


class CommitCollection(BaseModel):
    totalCount: int
    cursor: Optional[str]
    items: List[Commit] = []


class Resource(ResourceBase):
    """API Access class for commits"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )