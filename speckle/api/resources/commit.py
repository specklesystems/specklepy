from typing import Optional, List
from gql import gql
from pydantic.main import BaseModel
from speckle.api.resource import ResourceBase
from speckle.api.models import Commit


NAME = "commit"
METHODS = []


class Resource(ResourceBase):
    """API Access class for commits"""

    def __init__(self, me, basepath, client) -> None:
        super().__init__(
            me=me, basepath=basepath, client=client, name=NAME, methods=METHODS
        )
        self.schema = Commit