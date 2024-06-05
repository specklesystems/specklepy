"""Some useful helpers for working with automation data."""
import secrets
import string

from gql import gql
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from speckle_automate.schema import AutomationRunData, TestAutomationRunData
from specklepy.api.client import SpeckleClient


class TestAutomationEnvironment(BaseSettings):
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


def get_test_automation_environment() -> TestAutomationEnvironment:
    """Get known environment variables from local `.env` file"""

    return TestAutomationEnvironment().model_dump()


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

    return (
        result.get("projectMutations")
        .get("automationMutations")
        .get("createTestAutomationRun")
    )


def create_test_automation_run_data(
    speckle_client: SpeckleClient,
    speckle_server_url: str,
    project_id: str,
    test_automation_id: str,
) -> AutomationRunData:
    """Create automation run data for a new run for a given test automation"""

    test_automation_run_data = create_test_automation_run(
        speckle_client, project_id, test_automation_id
    )

    return AutomationRunData(
        project_id=project_id,
        speckle_server_url=speckle_server_url,
        automation_id=test_automation_id,
        automation_run_id=test_automation_run_data.get("automation_run_id"),
        function_run_id=test_automation_run_data.get("function_run_id"),
        triggers=test_automation_run_data.get("triggers"),
    )


def crypto_random_string(length: int) -> str:
    """Generate a semi crypto random string of a given length."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length)).lower()
