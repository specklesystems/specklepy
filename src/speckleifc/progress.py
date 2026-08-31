from __future__ import annotations

from typing import Protocol


class ProgressReporter(Protocol):
    def report(self, progress_message: str, progress: float | None) -> object: ...

    def should_report_progress(self) -> bool: ...
