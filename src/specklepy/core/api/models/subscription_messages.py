from specklepy.core.api.enums import (
    ProjectModelIngestionUpdatedMessageType,
    ProjectModelsUpdatedMessageType,
    ProjectUpdatedMessageType,
    ProjectVersionsUpdatedMessageType,
    UserProjectsUpdatedMessageType,
)
from specklepy.core.api.models.current import Model, ModelIngestion, Project, Version
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UserProjectsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: UserProjectsUpdatedMessageType
    project: Project | None


class ProjectModelsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectModelsUpdatedMessageType
    model: Model | None


class ProjectUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectUpdatedMessageType
    project: Project | None


class ProjectVersionsUpdatedMessage(GraphQLBaseModel):
    id: str
    type: ProjectVersionsUpdatedMessageType
    model_id: str
    version: Version | None


class ProjectModelIngestionUpdatedMessage(GraphQLBaseModel):
    model_ingestion: ModelIngestion
    type: ProjectModelIngestionUpdatedMessageType
