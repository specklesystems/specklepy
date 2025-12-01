from typing import Any, Optional, Tuple

from gql import Client, gql

from specklepy.api.credentials import Account
from specklepy.core.api.inputs.ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionRequestCancellationInput,
    ModelIngestionSuccessInput,
    ModelIngestionUpdateInput,
)
from specklepy.core.api.models.current import (
    ModelIngestion,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "ingestion"


class IngestionResource(ResourceBase):
    """API Access class for ingestionns"""

    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        server_version: Optional[Tuple[Any, ...]],
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def create(self, input: ModelIngestionCreateInput) -> ModelIngestion:
        QUERY = gql(
            """
            mutation IngestionCreate($input: ModelIngestionCreateInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: create(input: $input) {
                    id
                    createdAt
                    updatedAt
                  }
                }
              }
            }
           """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelIngestion]]], QUERY, variables
        ).data.data.data

    def update_progress(self, input: ModelIngestionUpdateInput) -> ModelIngestion:
        QUERY = gql(
            """
            mutation IngestionUpdateProgress(
              $input: ModelIngestionUpdateInput!
            ) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: updateProgress(input: $input) {
                    id
                    createdAt
                    updatedAt
                  }
                }
              }
            }
           """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelIngestion]]], QUERY, variables
        ).data.data.data

    def complete(self, input: ModelIngestionSuccessInput) -> str:
        """
        Request that the server completes the ingestion by creating a version
        If successful, the job will be in a terminal "successful" state.

        For failed Ingestions, use `fail_with_error` instead
        For user cancellation, use `fail_with_cancelled` instead

        Arguments:
            input {ModelIngestionSuccessInput} -- input variable

        Returns:
            str -- the id of the version that was just created to complete the ingestion
        """
        QUERY = gql(
            """
            mutation IngestionComplete($input: ModelIngestionSuccessInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: completeWithVersion(input: $input) {
                    data:statusData {
                      ... on ModelIngestionSuccessStatus {
                        versionId
                      }
                    }
                  }
                }
              }
            }
           """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[DataResponse[str]]]],
            QUERY,
            variables,
        ).data.data.data.data

    def fail_with_error(self, input: ModelIngestionFailedInput) -> ModelIngestion:
        """
        Fail the job with an error.
        For user cancellation, use `fail_with_cancelled` instead
        """
        QUERY = gql(
            """
            mutation IngestionFailWithError($input: ModelIngestionFailedInput!) {
              data: projectMutations {
                data: IngestionFailWithError {
                  data: failWithError(input: $input) {
                    id
                    createdAt
                    updatedAt
                  }
                }
              }
            }
           """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelIngestion]]],
            QUERY,
            variables,
        ).data.data.data

    def fail_with_cancel(self, input: ModelIngestionCancelledInput) -> ModelIngestion:
        """
        Fail the job with a `cancelled` status.
        This should only done if the user has explicitly requested cancellation
        Other forms of cancellation see `fail_with_error`
        """
        QUERY = gql(
            """
            mutation IngestionFailWithCancel($input: ModelIngestionCancelledInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: failWithCancel(input: $input) {
                    id
                    createdAt
                    updatedAt
                  }
                }
              }
            }
           """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelIngestion]]],
            QUERY,
            variables,
        ).data.data.data

    def request_cancellation(
        self, input: ModelIngestionRequestCancellationInput
    ) -> ModelIngestion:
        """
        Request that the ingestion is cancelled.

        Note it's up to the client to observe this cancellation request
        (via `subscription.project_model_ingestion_cancellation_requested`)
        and report it as cancelled via `ingestion.fail_with_cancelled`.

        See "cooperative cancellation pattern"
        """
        QUERY = gql(
            """
            mutation IngestionRequestCancellation($input: ModelIngestionRequestCancellationInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: requestCancellation (input: $input) {
                    id
                    createdAt
                    updatedAt
                  }
                }
              }
            }
           """  # noqa: E501
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelIngestion]]],
            QUERY,
            variables,
        ).data.data.data
