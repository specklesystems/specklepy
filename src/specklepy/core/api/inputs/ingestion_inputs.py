from typing import Any

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class IngestCreateInput(GraphQLBaseModel):
    file_name: str
    max_idle_timeout_minutes: int | None
    model_id: str
    project_id: str
    source_application: str
    source_application_version: str
    source_file_data: dict[str, Any]


class IngestFinishInput(GraphQLBaseModel):
    id: str
    message: str | None
    object_id: str
    project_id: str


class IngestErrorInput(GraphQLBaseModel):
    id: str
    error_reason: str | None
    error_stacktrace: str
    project_id: str


class CancelRequestInput(GraphQLBaseModel):
    id: str
    project_id: str


class IngestUpdateInput(GraphQLBaseModel):
    id: str
    progress: float | None
    progress_message: str
    project_id: str
