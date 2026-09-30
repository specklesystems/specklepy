"""OpenTelemetry spans for specklepy operations.

specklepy depends on ``opentelemetry-api`` only: without a configured SDK every span
is a no-op. A host that installs a tracer provider (the converter's dispatch, an
Automate function, a script) gets the spans as children of its own trace.
"""

from __future__ import annotations

import importlib.metadata
from contextlib import contextmanager
from typing import Iterator, Mapping

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.util.types import AttributeValue


def _version() -> str | None:
    try:
        return importlib.metadata.version("specklepy")
    except importlib.metadata.PackageNotFoundError:
        return None


_tracer = trace.get_tracer("specklepy", _version())


@contextmanager
def start_activity(
    name: str, attributes: Mapping[str, AttributeValue | None] | None = None
) -> Iterator[Span]:
    """A span that ends Ok on success, or records the exception and ends Error."""
    with _tracer.start_as_current_span(
        name,
        attributes={k: v for k, v in (attributes or {}).items() if v is not None},
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except BaseException as ex:
            span.record_exception(ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
            raise
        span.set_status(Status(StatusCode.OK))
