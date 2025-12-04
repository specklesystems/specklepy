from specklepy.core.api.enums import ProjectModelIngestionUpdatedMessageType
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class SourceDataInput(GraphQLBaseModel):
    source_application_slug: str
    source_application_version: str
    file_name: str | None
    file_size_bytes: int | None


class ModelIngestionCreateInput(GraphQLBaseModel):
    model_id: str
    project_id: str
    progress_message: str
    source_data: SourceDataInput


class ModelIngestionStartProcessingInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    progress_message: str
    source_data: SourceDataInput


class ModelIngestionRequeueInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    progress_message: str


class ModelIngestionUpdateInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    progress: float | None
    progress_message: str


class ModelIngestionSuccessInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    root_object_id: str


class ModelIngestionFailedInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    error_reason: str
    error_stacktrace: str | None

    @staticmethod
    def from_exception(
        ingestion_id: str, project_id: str, exception: Exception, message: str | None
    ) -> "ModelIngestionFailedInput":
        """test"""
        return ModelIngestionFailedInput(
            ingestion_id=ingestion_id,
            project_id=project_id,
            error_reason=message if message else str(exception),
            error_stacktrace=str(exception),
        )


class ModelIngestionCancelledInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    cancellation_message: str


class ModelIngestionRequestCancellationInput(GraphQLBaseModel):
    ingestion_id: str
    project_id: str
    cancellation_message: str


class ModelIngestionReference(GraphQLBaseModel):
    """
    `@oneOf` i.e. server expects **either** `ingestion_id` or `model_id`, but not both.
    """

    ingestion_id: str | None
    model_id: str | None


class ProjectModelIngestionSubscriptionInput(GraphQLBaseModel):
    project_id: str
    ingestion_reference: ModelIngestionReference
    message_type: ProjectModelIngestionUpdatedMessageType | None = None
