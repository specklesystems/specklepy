from specklepy.core.api.inputs.ingestion_inputs import (
    CancelRequestInput,
    IngestCreateInput,
    IngestErrorInput,
    IngestFinishInput,
    IngestUpdateInput,
)
from specklepy.core.api.models.current import (
    Ingestion,
    ResourceCollection,
    Version,
)
from specklepy.core.api.resources import (
    IngestionResource as CoreResource,
)
from specklepy.logging import metrics


class IngestionResource(CoreResource):
    """API Access class for ingestionns"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(account, basepath, client, server_version)

    def get_ingestions(
        self, model_id: str, project_id: str
    ) -> ResourceCollection[Ingestion]:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Get Ingestions"})
        return super().get_ingestions(model_id, project_id)

    def update(self, input: IngestUpdateInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Update"})
        return super().update(input)

    def create(self, input: IngestCreateInput) -> Ingestion:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Create"})
        return super().create(input)

    def end(self, input: IngestFinishInput) -> Version:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion End"})
        return super().end(input)

    def error(self, input: IngestErrorInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Error"})
        return super().error(input)

    def cancel(self, input: CancelRequestInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Ingestion Cancel"})
        return super().cancel(input)
