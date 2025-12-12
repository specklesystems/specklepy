from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionRequeueInput,
    ModelIngestionStartProcessingInput,
    ModelIngestionSuccessInput,
    ModelIngestionUpdateInput,
)
from specklepy.core.api.models.current import (
    ModelIngestion,
)
from specklepy.core.api.resources import (
    ModelIngestionResource as CoreResource,
)
from specklepy.logging import metrics


class ModelIngestionResource(CoreResource):
    """API Access class for model ingestion"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(account, basepath, client, server_version)

    def create(self, input: ModelIngestionCreateInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Create"})
        return super().create(input)

    def get_ingestion(self, project_id: str, model_ingestion_id: str) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Get"})
        return super().get_ingestion(project_id, model_ingestion_id)

    def update_progress(self, input: ModelIngestionUpdateInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Update"})
        return super().update_progress(input)

    def start_processing(
        self, input: ModelIngestionStartProcessingInput
    ) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Start Processing"})
        return super().start_processing(input)

    def requeue(self, input: ModelIngestionRequeueInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Update"})
        return super().requeue(input)

    def complete(self, input: ModelIngestionSuccessInput) -> str:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion End"})
        return super().complete(input)

    def fail_with_error(self, input: ModelIngestionFailedInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Error"})
        return super().fail_with_error(input)

    def fail_with_cancel(self, input: ModelIngestionCancelledInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Cancel"})
        return super().fail_with_cancel(input)
