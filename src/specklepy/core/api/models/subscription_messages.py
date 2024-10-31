from typing import Optional

from pydantic import BaseModel

from specklepy.core.api.enums import (
    ProjectModelsUpdatedMessageType,
    ProjectUpdatedMessageType,
    ProjectVersionsUpdatedMessageType,
    UserProjectsUpdatedMessageType,
)
from specklepy.core.api.models.current import Model, Project, Version


class UserProjectsUpdatedMessage(BaseModel):
    id: str
    type: UserProjectsUpdatedMessageType
    project: Optional[Project]


class ProjectModelsUpdatedMessage(BaseModel):
    id: str
    type: ProjectModelsUpdatedMessageType
    model: Optional[Model]


class ProjectUpdatedMessage(BaseModel):
    id: str
    type: ProjectUpdatedMessageType
    project: Optional[Project]


class ProjectVersionsUpdatedMessage(BaseModel):
    id: str
    type: ProjectVersionsUpdatedMessageType
    modelId: Optional[str]
    version: Optional[Version]
