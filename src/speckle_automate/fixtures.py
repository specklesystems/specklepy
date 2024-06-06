"""Some useful helpers for working with automation data."""
import secrets
import string

import pytest
from gql import gql
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from speckle_automate.schema import AutomationRunData, TestAutomationRunData
from specklepy.api.client import SpeckleClient


class TestAutomationEnvironment(BaseSettings):
    """Get known environment variables from local `.env` file"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="speckle_",
        extra="ignore",
    )

    token: str = Field()
    server_url: str = Field()
    project_id: str = Field()
    automation_id: str = Field()


@pytest.fixture()
def test_automation_environment() -> TestAutomationEnvironment:
    return TestAutomationEnvironment()


@pytest.fixture()
def test_automation_token(
    test_automation_environment: TestAutomationEnvironment,
) -> str:
    """Provide a speckle token for the test suite."""

    return test_automation_environment.token


@pytest.fixture()
def speckle_client(
    test_automation_environment: TestAutomationEnvironment,
) -> SpeckleClient:
    """Initialize a SpeckleClient for testing."""
    speckle_client = SpeckleClient(
        test_automation_environment.server_url,
        test_automation_environment.server_url.startswith("https"),
    )
    speckle_client.authenticate_with_token(test_automation_environment.token)
    return speckle_client


def create_test_automation_run(
    speckle_client: SpeckleClient, project_id: str, test_automation_id: str
) -> TestAutomationRunData:
    """Create test run to report local test results to"""

    query = gql(
        """
        mutation CreateTestRun(
            $projectId: ID!,
            $automationId: ID!
        ) {
            projectMutations {
                automationMutations(projectId: $projectId) {
                    createTestAutomationRun(automationId: $automationId) {
                        automationRunId
                        functionRunId
                        triggers {
                            payload {
                                modelId
                                versionId
                            }
                            triggerType
                        }
                    }
                }
            }
        }
        """
    )

    params = {"automationId": test_automation_id, "projectId": project_id}

    result = speckle_client.httpclient.execute(query, params)

    print(result)

    return (
        result.get("projectMutations")
        .get("automationMutations")
        .get("createTestAutomationRun")
    )


@pytest.fixture()
def test_automation_run(
    speckle_client: SpeckleClient,
    test_automation_environment: TestAutomationEnvironment,
) -> TestAutomationRunData:
    return create_test_automation_run(
        speckle_client,
        test_automation_environment.project_id,
        test_automation_environment.automation_id,
    )


def create_test_automation_run_data(
    speckle_client: SpeckleClient,
    test_automation_environment: TestAutomationEnvironment,
) -> AutomationRunData:
    """Create automation run data for a new run for a given test automation"""

    test_automation_run_data = create_test_automation_run(
        speckle_client,
        test_automation_environment.project_id,
        test_automation_environment.automation_id,
    )

    return AutomationRunData(
        project_id=test_automation_environment.project_id,
        speckle_server_url=test_automation_environment.server_url,
        automation_id=test_automation_environment.automation_id,
        automation_run_id=test_automation_run_data["automationRunId"],
        function_run_id=test_automation_run_data["functionRunId"],
        triggers=test_automation_run_data["triggers"],
    )


@pytest.fixture()
def test_automation_run_data(
    speckle_client: SpeckleClient,
    test_automation_environment: TestAutomationEnvironment,
) -> AutomationRunData:
    return create_test_automation_run_data(speckle_client, test_automation_environment)


def crypto_random_string(length: int) -> str:
    """Generate a semi crypto random string of a given length."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length)).lower()


__all__ = [
    "test_automation_environment",
    "test_automation_token",
    "speckle_client",
    "test_automation_run",
    "test_automation_run_data",
]
