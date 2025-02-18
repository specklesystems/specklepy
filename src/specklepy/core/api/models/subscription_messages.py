from typing import Optional

from specklepy.core.api.enums import (
    ProjectModelsUpdatedMessageType,
    ProjectUpdatedMessageType,
    ProjectVersionsUpdatedMessageType,
    UserProjectsUpdatedMessageType,
)
from specklepy.core.api.models.current import Model, Project, Version
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UserProjectsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: UserProjectsUpdatedMessageType
    project: Optional[Project]


class ProjectModelsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectModelsUpdatedMessageType
    model: Optional[Model]


class ProjectUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectUpdatedMessageType
    project: Optional[Project]


class ProjectVersionsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectVersionsUpdatedMessageType
    model_id: str
    version: Optional[Version]
