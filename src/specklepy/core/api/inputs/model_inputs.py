from typing import Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class CreateModelInput(GraphQLBaseModel):
    name: str
    description: str | None = None
    project_id: str


class DeleteModelInput(GraphQLBaseModel):
    id: str
    project_id: str


class UpdateModelInput(GraphQLBaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    project_id: str


class ModelVersionsFilter(GraphQLBaseModel):
    priority_ids: Sequence[str]
    priority_ids_only: bool | None = None
