from typing import Optional, Sequence

from pydantic import BaseModel


class CreateModelInput(BaseModel):
    name: str
    description: Optional[str] = None
    projectId: str


class DeleteModelInput(BaseModel):
    id: str
    projectId: str


class UpdateModelInput(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    projectId: str


class ModelVersionsFilter(BaseModel):
    priorityIds: Sequence[str]
    priorityIdsOnly: Optional[bool] = None
