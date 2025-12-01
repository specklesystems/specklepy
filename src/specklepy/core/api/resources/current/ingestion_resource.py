from typing import Any, Optional, Tuple

from gql import Client, gql

from specklepy.api.credentials import Account
from specklepy.core.api.inputs.ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
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

    def fail_with_cancelled(
        self, input: ModelIngestionCancelledInput
    ) -> ModelIngestion:
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
