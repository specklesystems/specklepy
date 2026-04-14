from typing import Dict, List

from specklepy.progress.ingestion_progress import IngestionProgressManager
from specklepy.transports.abstract_transport import AbstractTransport


class ProgressTransport(AbstractTransport):
    """
    This transport does not persist objects anywhere,
    instead it simply reacts to save_object being called,
    and reports throttled progress.
    """

    def __init__(
        self,
        progress: IngestionProgressManager,
        name="Progress",
        progress_message_template="Uploading objects {:,}",
    ) -> None:
        super().__init__()
        self._name = name
        self._progress = progress
        self._progress_message_template = progress_message_template
        self.saved_object_count = 0

    def _throttle_progress(self) -> None:
        if self._progress.should_report_progress():
            self._progress.report(
                self._progress_message_template.format(self.saved_object_count), None
            )

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"ProgressTransport(objects: {self.saved_object_count})"

    def save_object(self, id: str, serialized_object: str) -> None:
        self.saved_object_count += 1
        self._throttle_progress()

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        self.saved_object_count += 1
        self._throttle_progress()

    def get_object(self, id: str) -> str | None:
        return None

    def has_objects(self, id_list: List[str]) -> Dict[str, bool]:
        return {id: False for id in id_list}

    def begin_write(self) -> None:
        self.saved_object_count = 0

    def end_write(self) -> None:
        pass

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        raise NotImplementedError
