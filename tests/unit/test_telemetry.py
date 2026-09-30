from unittest.mock import MagicMock

import pytest
from gql import gql
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode
from pydantic import BaseModel

from specklepy.api.resource import ResourceBase
from specklepy.logging.exceptions import SpeckleException
from specklepy.logging.telemetry import start_activity

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture(autouse=True)
def spans() -> InMemorySpanExporter:
    _exporter.clear()
    return _exporter


def test_activity_ends_ok_with_attributes(spans: InMemorySpanExporter):
    with start_activity("Test.Ok", {"speckle.projectId": "p", "skipped": None}) as a:
        a.set_attribute("speckle.versionId", "v")

    (span,) = spans.get_finished_spans()
    assert span.name == "Test.Ok"
    assert span.status.status_code == StatusCode.OK
    assert dict(span.attributes or {}) == {
        "speckle.projectId": "p",
        "speckle.versionId": "v",
    }


def test_activity_records_exception_and_ends_error(spans: InMemorySpanExporter):
    with pytest.raises(ValueError), start_activity("Test.Error"):
        raise ValueError("boom")

    (span,) = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert [e.name for e in span.events] == ["exception"]


def test_activities_nest_under_the_host_span(spans: InMemorySpanExporter):
    tracer = trace.get_tracer("host")
    with tracer.start_as_current_span("host") as host, start_activity("Test.Child"):
        pass

    child, _ = spans.get_finished_spans()
    assert child.parent is not None
    assert child.parent.span_id == host.get_span_context().span_id


class _Echo(BaseModel):
    value: int


def _resource(client: MagicMock) -> ResourceBase:
    return ResourceBase(
        account=MagicMock(), basepath="", client=client, name="test_resource"
    )


def test_graphql_request_span_omits_variables(spans: InMemorySpanExporter):
    client = MagicMock()
    client.execute.return_value = {"value": 1}
    request = gql("query Echo($token: String!) { echo(token: $token) }")
    request.variable_values = {"token": "secret"}

    _resource(client).make_request_and_parse_response(_Echo, request)

    (span,) = spans.get_finished_spans()
    attributes = dict(span.attributes or {})
    assert span.name == "GraphQL.Request"
    assert attributes["speckle.resource"] == "test_resource"
    assert attributes["responseType"] == "_Echo"
    assert "secret" not in str(attributes)


def test_graphql_request_span_records_failure(spans: InMemorySpanExporter):
    client = MagicMock()
    client.execute.side_effect = RuntimeError("down")

    with pytest.raises(SpeckleException):
        _resource(client).make_request_and_parse_response(_Echo, gql("{ a }"))

    (span,) = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
