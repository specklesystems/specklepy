from unittest.mock import MagicMock

import pytest

from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionSuccessInput,
)
from specklepy.core.api.resources.current.model_ingestion_resource import (
    ModelIngestionResource,
)
from specklepy.logging.exceptions import SpeckleException


def _resource() -> tuple[ModelIngestionResource, MagicMock]:
    client = MagicMock()
    resource = ModelIngestionResource(
        account=MagicMock(), basepath="", client=client, server_version=None
    )
    return resource, client


def _complete_response(status_data: dict) -> dict:
    return {"data": {"data": {"data": {"data": status_data}}}}


def _input() -> ModelIngestionSuccessInput:
    return ModelIngestionSuccessInput(
        project_id="project-id",
        ingestion_id="ingestion-id",
        root_object_id="root-id",
        version_message=None,
    )


def test_complete_success_returns_version_id_without_follow_up():
    resource, client = _resource()
    client.execute.return_value = _complete_response(
        {"__typename": "ModelIngestionSuccessStatus", "versionId": "version-id"}
    )

    assert resource.complete(_input()) == "version-id"
    assert client.execute.call_count == 1


def test_complete_processing_fetches_reserved_version_id():
    resource, client = _resource()
    client.execute.side_effect = [
        _complete_response(
            {
                "__typename": "ModelIngestionProcessingStatus",
                "progressMessage": "still going",
            }
        ),
        {"data": {"data": {"data": "reserved-id"}}},
    ]

    assert resource.complete(_input()) == "reserved-id"
    assert client.execute.call_count == 2
    (request,), _ = client.execute.call_args
    assert request.variable_values == {
        "projectId": "project-id",
        "modelIngestionId": "ingestion-id",
    }


def test_complete_processing_without_reserved_id_raises():
    resource, client = _resource()
    client.execute.side_effect = [
        _complete_response({"__typename": "ModelIngestionProcessingStatus"}),
        {"data": {"data": {"data": None}}},
    ]

    with pytest.raises(SpeckleException):
        resource.complete(_input())


def test_complete_failed_raises_with_error_reason():
    resource, client = _resource()
    client.execute.return_value = _complete_response(
        {"__typename": "ModelIngestionFailedStatus", "errorReason": "boom"}
    )

    with pytest.raises(SpeckleException, match="boom"):
        resource.complete(_input())
    assert client.execute.call_count == 1
