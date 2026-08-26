from typing import Any, Tuple

from gql import Client, gql
from pydantic import BaseModel, Field

from specklepy.api.credentials import Account
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionRequestCancellationInput,
    ModelIngestionRequeueInput,
    ModelIngestionStartProcessingInput,
    ModelIngestionSuccessInput,
    ModelIngestionUpdateInput,
)
from specklepy.core.api.models.current import (
    ModelIngestion,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import SpeckleException

NAME = "ingestion"


class _CompleteStatusData(BaseModel):
    """statusData fragments selected by `complete`, discriminated by typename."""

    typename: str = Field(alias="__typename")
    version_id: str | None = Field(default=None, alias="versionId")
    progress_message: str | None = Field(default=None, alias="progressMessage")
    error_reason: str | None = Field(default=None, alias="errorReason")


class ModelIngestionResource(ResourceBase):
    """API Access class for model ingestion"""

    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        server_version: Tuple[Any, ...] | None,
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def get_ingestion(self, project_id: str, model_ingestion_id: str) -> ModelIngestion:
        QUERY = gql(
            """
            query Query($projectId: String!, $modelIngestionId: ID!) {
              data:project(id: $projectId) {
                data:ingestion(id: $modelIngestionId) {
                  id
                  createdAt
                  updatedAt
                  modelId
                  projectId
                  userId
                  cancellationRequested
                  statusData {
                    ... on HasModelIngestionStatus {
                      status
                    }
                    ... on HasProgressMessage {
                      progressMessage
                    }
                    ... on ModelIngestionSuccessStatus
                    {
                      versionId
                    }
                  }
                }
              }
            }
            """  # noqa: E501
        )

        variables = {
            "projectId": project_id,
            "modelIngestionId": model_ingestion_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ModelIngestion]],
            QUERY,
            variables,
        ).data.data

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
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
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
            DataResponse[DataResponse[DataResponse[ModelIngestion]]], QUERY, variables
        ).data.data.data

    def start_processing(
        self, input: ModelIngestionStartProcessingInput
    ) -> ModelIngestion:
        QUERY = gql(
            """
            mutation IngestionStartProcessing($input: ModelIngestionStartProcessingInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: startProcessing(input: $input) {
                    id
                    createdAt
                    updatedAt
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
                      }
                    }
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
            DataResponse[DataResponse[DataResponse[ModelIngestion]]], QUERY, variables
        ).data.data.data

    def requeue(self, input: ModelIngestionRequeueInput) -> ModelIngestion:
        QUERY = gql(
            """
            mutation IngestionRequeue($input: ModelIngestionRequeueInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: requeue(input: $input) {
                    id
                    createdAt
                    updatedAt
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
                      }
                    }
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
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
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
            DataResponse[DataResponse[DataResponse[ModelIngestion]]], QUERY, variables
        ).data.data.data

    def get_reserved_version_id(
        self, project_id: str, model_ingestion_id: str
    ) -> str | None:
        """
        Read the id the server reserved for the version this ingestion will produce.

        Selects the top-level `ModelIngestion.versionId`, which only exists on
        servers where every version entry point is an ingestion (2026.9+, ENG-9314).
        On older servers the query fails validation, so only call this when the
        server has signalled it (see `complete`).

        Returns:
            str | None -- the reserved version id, None if none was reserved
        """
        QUERY = gql(
            """
            query IngestionReservedVersionId(
              $projectId: String!, $modelIngestionId: ID!
            ) {
              data:project(id: $projectId) {
                data:ingestion(id: $modelIngestionId) {
                  data:versionId
                }
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
            "modelIngestionId": model_ingestion_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[str | None]]],
            QUERY,
            variables,
        ).data.data.data

    def complete(self, input: ModelIngestionSuccessInput) -> str:
        """
        Request that the server completes the ingestion by creating a version.

        On servers up to 2026.8 the ingestion is in a terminal "successful" state
        when this returns and the version exists. From server 2026.9 (ENG-9314)
        the server may answer with the ingestion still processing; in that case
        the returned id is the one reserved for the version and the version is
        not visible yet. Callers that need the version to exist should poll
        `project.modelIngestions` (or `get_ingestion`) for a terminal status.

        For failed Ingestions, use `fail_with_error` instead
        For user cancellation, use `fail_with_cancelled` instead

        Arguments:
            input {ModelIngestionSuccessInput} -- input variable

        Returns:
            str -- the id of the version created (or reserved) for this ingestion

        Raises:
            SpeckleException -- the server reported the ingestion as failed
        """
        QUERY = gql(
            """
            mutation IngestionComplete($input: ModelIngestionSuccessInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: completeWithVersion(input: $input) {
                    data:statusData {
                      __typename
                      ... on ModelIngestionSuccessStatus {
                        versionId
                      }
                      ... on ModelIngestionProcessingStatus {
                        progressMessage
                      }
                      ... on ModelIngestionFailedStatus {
                        errorReason
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

        status = self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[DataResponse[_CompleteStatusData]]]],
            QUERY,
            variables,
        ).data.data.data.data

        if status.typename == "ModelIngestionSuccessStatus":
            if status.version_id is None:
                raise SpeckleException(
                    "Ingestion completed but the server returned no version id"
                )
            return status.version_id

        if status.typename == "ModelIngestionProcessingStatus":
            version_id = self.get_reserved_version_id(
                input.project_id, input.ingestion_id
            )
            if version_id is None:
                raise SpeckleException(
                    "Ingestion is still processing and the server reserved no"
                    " version id"
                )
            return version_id

        if status.typename == "ModelIngestionFailedStatus":
            raise SpeckleException(status.error_reason or "Ingestion failed")

        raise SpeckleException(
            f"Unexpected ingestion status type from completeWithVersion:"
            f" {status.typename}"
        )

    def fail_with_error(self, input: ModelIngestionFailedInput) -> ModelIngestion:
        """
        Fail the job with an error.
        For user requested cancellation, use `fail_with_cancelled` instead
        """
        QUERY = gql(
            """
            mutation IngestionFailWithError($input: ModelIngestionFailedInput!) {
              data: projectMutations {
                data: modelIngestionMutations {
                  data: failWithError(input: $input) {
                    id
                    createdAt
                    updatedAt
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
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
            DataResponse[DataResponse[DataResponse[ModelIngestion]]],
            QUERY,
            variables,
        ).data.data.data

    def fail_with_cancel(self, input: ModelIngestionCancelledInput) -> ModelIngestion:
        """
        Fail the ingestion with a `cancelled` status.
        This should only be done if the user has explicitly requested cancellation
        Other forms of cancellation use `fail_with_error`
        The ingestion should then enter a terminal "canceled" state
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
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
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
            DataResponse[DataResponse[DataResponse[ModelIngestion]]],
            QUERY,
            variables,
        ).data.data.data

    def request_cancellation(
        self, input: ModelIngestionRequestCancellationInput
    ) -> ModelIngestion:
        """
        Request that the ingestion is canceled.

        Note: simply calling this mutation does not immediately cancel,
        it doesn't even guarantee it will be canceled at all.
        It's up to the client to observe this cancellation request
        via `subscription.project_model_ingestion_cancellation_requested`
        and report it as cancelled (via `ingestion.fail_with_cancel`

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
                    modelId
                    projectId
                    userId
                    cancellationRequested
                    statusData {
                      ... on HasModelIngestionStatus {
                        status
                      }
                      ... on HasProgressMessage {
                        progressMessage
                      }
                    }
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
