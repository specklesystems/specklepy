from typing import Optional, Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UpdateVersionInput(GraphQLBaseModel):
    version_id: str
    project_id: str
    message: Optional[str]


class MoveVersionsInput(GraphQLBaseModel):
    target_model_name: str
    version_ids: Sequence[str]
    project_id: str


class DeleteVersionsInput(GraphQLBaseModel):
    version_ids: Sequence[str]
    project_id: str


class CreateVersionInput(GraphQLBaseModel):
    object_id: str
    model_id: str
    project_id: str
    message: Optional[str] = None
    source_application: Optional[str] = "py"
    total_children_count: Optional[int] = None
    parents: Optional[Sequence[str]] = None


class MarkReceivedVersionInput(GraphQLBaseModel):
    version_id: str
    project_id: str
    source_application: str
    message: Optional[str] = None
