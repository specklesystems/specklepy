"""Some useful helpers for working with automation data."""
import secrets
import string

from gql import gql

from specklepy.api.client import SpeckleClient


def register_new_automation(
    speckle_client: SpeckleClient,
    project_id: str,
    model_id: str,
    automation_id: str,
    automation_name: str,
    automation_revision_id: str,
) -> bool:
    """Register a new automation in the speckle server."""
    query = gql(
        """
        mutation CreateAutomation(
            $projectId: String!
            $modelId: String!
            $automationName: String!
            $automationId: String!
            $automationRevisionId: String!
        ) {
                automationMutations {
                    create(
                        input: {
                            projectId: $projectId
                            modelId: $modelId
                            automationName: $automationName
                            automationId: $automationId
                            automationRevisionId: $automationRevisionId
                        }
                    )
                }
            }
        """
    )
    params = {
        "projectId": project_id,
        "modelId": model_id,
        "automationName": automation_name,
        "automationId": automation_id,
        "automationRevisionId": automation_revision_id,
    }
    return speckle_client.httpclient.execute(query, params)


def crypto_random_string(length: int) -> str:
    """Generate a semi crypto random string of a given length."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length)).lower()
