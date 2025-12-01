from specklepy.core.api.inputs.ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionSuccessInput,
    ModelIngestionUpdateInput,
)
from specklepy.core.api.models.current import (
    ModelIngestion,
)
from specklepy.core.api.resources import (
    IngestionResource as CoreResource,
)
from specklepy.logging import metrics


class IngestionResource(CoreResource):
    """API Access class for ingestionns"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(account, basepath, client, server_version)

    def create(self, input: ModelIngestionCreateInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Create"})
        return super().create(input)

    def update_progress(self, input: ModelIngestionUpdateInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Update"})
        return super().update_progress(input)

    def complete_successfully(self, input: ModelIngestionSuccessInput) -> str:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion End"})
        return super().complete(input)

    def complete_failed(self, input: ModelIngestionFailedInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Error"})
        return super().fail_with_error(input)

    def fail_with_cancel(self, input: ModelIngestionCancelledInput) -> ModelIngestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Cancel"})
        return super().fail_with_cancel(input)
