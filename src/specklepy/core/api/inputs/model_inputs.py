from typing import Optional, Sequence

from pydantic import BaseModel


class CreateModelInput(BaseModel):
    name: str
    description: Optional[str]
    projectId: str


class DeleteModelInput(BaseModel):
    id: str
    projectId: str


class UpdateModelInput(BaseModel):
    id: str
    name: Optional[str]
    description: Optional[str]
    projectId: str


class ModelVersionsFilter(BaseModel):
    priorityIds: Sequence[str]
    priorityIdsOnly: Optional[bool]
