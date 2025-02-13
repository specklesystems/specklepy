from typing import Optional, Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class CreateModelInput(GraphQLBaseModel):
    name: str
    description: Optional[str] = None
    project_id: str


class DeleteModelInput(GraphQLBaseModel):
    id: str
    project_id: str


class UpdateModelInput(GraphQLBaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: str


class ModelVersionsFilter(GraphQLBaseModel):
    priority_ids: Sequence[str]
    priority_ids_only: Optional[bool] = None
