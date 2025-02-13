"""Run integration tests with a speckle server."""

import os
from pathlib import Path
from typing import Dict

import pytest
from gql import gql

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function,
)
from speckle_automate.fixtures import (
    create_test_automation_run_data,
    crypto_random_string,
)
from speckle_automate.schema import AutomateBase
from specklepy.api.client import SpeckleClient
from specklepy.core.api.models.current import Model, Version
from specklepy.objects.base import Base


@pytest.fixture
def speckle_token(user_dict: Dict[str, str]) -> str:
    """Provide a speckle token for the test suite."""
    return user_dict["token"]


@pytest.fixture
def speckle_server_url(host: str) -> str:
    """Provide a speckle server url for the test suite, default to localhost."""
    return f"http://{host}"


@pytest.fixture
def test_client(speckle_server_url: str, speckle_token: str) -> SpeckleClient:
    """Initialize a SpeckleClient for testing."""
    test_client = SpeckleClient(speckle_server_url, use_ssl=False)
    test_client.authenticate_with_token(speckle_token)
    return test_client


@pytest.fixture
def automation_run_data(
    test_client: SpeckleClient, speckle_server_url: str
) -> AutomationRunData:
    """TODO: Set up a test automation for integration testing"""
    project_id = crypto_random_string(10)
    test_automation_id = crypto_random_string(10)

    return create_test_automation_run_data(
        test_client, speckle_server_url, project_id, test_automation_id
    )


@pytest.fixture
def automation_context(
    automation_run_data: AutomationRunData, speckle_token: str
) -> AutomationContext:
    """Set up the run context."""
    return AutomationContext.initialize(automation_run_data, speckle_token)


def get_automation_status(
    project_id: str,
    model_id: str,
    speckle_client: SpeckleClient,
):
    query = gql(
        """
query AutomationRuns(
            $projectId: String!
            $modelId: String!
    )
{
  project(id: $projectId) {
    model(id: $modelId) {
      automationStatus {
        id
        status
        statusMessage
        automationRuns {
          id
          automationId
          versionId
          createdAt
          updatedAt
          status
          functionRuns {
            id
            functionId
            elapsed
            status
            contextView
            statusMessage
            results
            resultVersions {
              id
            }
          }
        }
      }
    }
  }
}
        """
    )
    params = {
        "projectId": project_id,
        "modelId": model_id,
    }
    response = speckle_client.httpclient.execute(query, params)
    return response["project"]["model"]["automationStatus"]


class FunctionInputs(AutomateBase):
    forbidden_speckle_type: str


def automate_function(
    automation_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """Hey, trying the automate sdk experience here."""
    version_root_object = automation_context.receive_version()

    count = 0
    if version_root_object.speckle_type == function_inputs.forbidden_speckle_type:
        if not version_root_object.id:
            raise ValueError("Cannot operate on objects without their id's.")
        automation_context.attach_error_to_objects(
            "Forbidden speckle_type",
            version_root_object.id,
            "This project should not contain the type: "
            f"{function_inputs.forbidden_speckle_type}",
        )
        count += 1

    if count > 0:
        automation_context.mark_run_failed(
            "Automation failed: "
            f"Found {count} object that have a forbidden speckle type: "
            f"{function_inputs.forbidden_speckle_type}"
        )

    else:
        automation_context.mark_run_success("No forbidden types found.")


@pytest.mark.skip(
    "currently the function run cannot be integration tested with the server"
)
def test_function_run(automation_context: AutomationContext) -> None:
    """Run an integration test for the automate function."""
    automation_context = run_function(
        automation_context,
        automate_function,
        FunctionInputs(forbidden_speckle_type="Base"),
    )

    assert automation_context.run_status == AutomationStatus.FAILED
    status = get_automation_status(
        automation_context.automation_run_data.project_id,
        automation_context.automation_run_data.model_id,
        automation_context.speckle_client,
    )
    assert status["status"] == automation_context.run_status
    status_message = status["automationRuns"][0]["functionRuns"][0]["statusMessage"]
    assert status_message == automation_context.status_message


@pytest.fixture
def test_file_path():
    path = Path(f"./{crypto_random_string(10)}").resolve()
    yield path
    os.remove(path)


@pytest.mark.skip(
    "currently the function run cannot be integration tested with the server"
)
def test_file_uploads(
    automation_run_data: AutomationRunData, speckle_token: str, test_file_path: Path
):
    """Test file store capabilities of the automate sdk."""
    automation_context = AutomationContext.initialize(
        automation_run_data, speckle_token
    )

    test_file_path.write_text("foobar")

    automation_context.store_file_result(test_file_path)

    assert len(automation_context._automation_result.blobs) == 1


@pytest.mark.skip(
    "currently the function run cannot be integration tested with the server"
)
def test_create_version_in_project_raises_error_for_same_model(
    automation_context: AutomationContext,
) -> None:
    with pytest.raises(ValueError):
        automation_context.create_new_version_in_project(
            Base(), automation_context.automation_run_data.branch_name
        )


@pytest.mark.skip(
    "currently the function run cannot be integration tested with the server"
)
def test_create_version_in_project(
    automation_context: AutomationContext,
) -> None:
    root_object = Base()
    root_object.foo = "bar"
    model, version = automation_context.create_new_version_in_project(
        root_object, "foobar"
    )
    isinstance(model, Model)
    isinstance(version, Version)


@pytest.mark.skip(
    "currently the function run cannot be integration tested with the server"
)
def test_set_context_view(automation_context: AutomationContext) -> None:
    automation_context.set_context_view()

    assert automation_context.context_view is not None
    assert automation_context.context_view.endswith(
        f"models/{automation_context.automation_run_data.model_id}@{automation_context.automation_run_data.version_id}"
    )

    automation_context.report_run_status()

    automation_context._automation_result.result_view = None

    dummy_context = "foo@bar"
    automation_context.set_context_view([dummy_context])

    assert automation_context.context_view is not None
    assert automation_context.context_view.endswith(
        f"models/{automation_context.automation_run_data.model_id}@{automation_context.automation_run_data.version_id},{dummy_context}"
    )
    automation_context.report_run_status()

    automation_context._automation_result.result_view = None

    dummy_context = "foo@baz"
    automation_context.set_context_view(
        [dummy_context], include_source_model_version=False
    )

    assert automation_context.context_view is not None
    assert automation_context.context_view.endswith(f"models/{dummy_context}")
    automation_context.report_run_status()
