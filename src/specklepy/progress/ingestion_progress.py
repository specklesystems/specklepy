from time import monotonic

from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.inputs.model_ingestion_inputs import ModelIngestionUpdateInput
from specklepy.core.api.models.current import ModelIngestion


class IngestionProgressManager:
    """
    Provides a performant way to report ingestion progress.

    Allows callers to throttle ingestion progress messages based on an update interval.
    Throttling prevents callers from overwhelming the server with constant progress updates,
    and minimises blocking high-speed operations with too frequent progress updates.

    Callers can use this pattern for reporting throttled progress
    ```
    if progress.should_report_progress():
        progress.report(f"Converting geometries ({current:,}/{total:,})", current - total)
    ```

    And for unthrottled progress (e.g. between phases)
    ```
    progress.report(f"Next phases has started (0/{total:,})", 0)

    This class is similar to the `IngestionProgressManager` in the .NET SDK
    Unlike in .NET, we recommend using a very coarse `update_interval_seconds`; since we're not using async messages,
    they are blocking and will degrade performance if used too frequently.
    ```

    """  # noqa: E501

    def __init__(
        self,
        speckle_client: SpeckleClient,
        ingestion: ModelIngestion,
        update_interval_seconds: float,
    ):
        self.speckle_client = speckle_client
        self.ingestion = ingestion
        self.update_interval = update_interval_seconds

        self._last_updated_at = 0.0

    def report(self, progress_message: str, progress: float | None) -> ModelIngestion:
        """
        Reports a progress update
        """
        self._last_updated_at = monotonic()
        formatted_progress = f"{progress:.0%}" if progress else ""
        print(f"Progress update: {progress_message} {formatted_progress}")

        return self.speckle_client.model_ingestion.update_progress(
            ModelIngestionUpdateInput(
                ingestion_id=self.ingestion.id,
                project_id=self.ingestion.project_id,
                progress_message=progress_message,
                progress=progress,
            )
        )

    def should_report_progress(self) -> bool:
        """
        Returns `true` if it's time for an update,
        `false` if it's too soon since the last update
        """
        elapsed = monotonic() - self._last_updated_at
        return elapsed >= self.update_interval
