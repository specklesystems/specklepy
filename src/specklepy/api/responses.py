from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T
