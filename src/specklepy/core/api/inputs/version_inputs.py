from typing import Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UpdateVersionInput(GraphQLBaseModel):
    version_id: str
    project_id: str
    message: str | None


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
    message: str | None = None
    source_application: str | None = "py"
    total_children_count: int | None = None
    parents: Sequence[str] | None = None


class MarkReceivedVersionInput(GraphQLBaseModel):
    version_id: str
    project_id: str
    source_application: str
    """
    IMPORTANT: this is meant to be the slug of the application that has done the
    receiving, not to be confused with `Version.sourceApplication`
    """
    message: str | None = None
