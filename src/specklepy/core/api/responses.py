from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

from specklepy.core.api.new_models import LimitedUser

T = TypeVar("T")


class ResourceCollection(BaseModel, Generic[T]):
    totalCount: int
    items: List[T]
    cursor: Optional[str] = None


class ProjectCommentCollection(ResourceCollection[T], Generic[T]):
    totalArchivedCount: int


class UserSearchResultCollection(BaseModel):
    items: List[LimitedUser]
    cursor: Optional[str] = None


class DataResponse(BaseModel, Generic[T]):
    data: T
