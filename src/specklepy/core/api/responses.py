from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResourceCollection(BaseModel, Generic[T]):
    totalCount: int
    items: List[T]
    cursor: Optional[str] = None


class ProjectCommentCollection(ResourceCollection[T], Generic[T]):
    totalArchivedCount: int


class DataResponse(BaseModel, Generic[T]):
    data: T
