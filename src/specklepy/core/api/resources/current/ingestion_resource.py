from typing import Any, Optional, Tuple

from gql import Client, gql

from specklepy.api.credentials import Account
from specklepy.core.api.inputs.ingestion_inputs import (
    CancelRequestInput,
    IngestCreateInput,
    IngestErrorInput,
    IngestFinishInput,
    IngestUpdateInput,
)
from specklepy.core.api.models.current import (
    Ingestion,
    ResourceCollection,
    Version,
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

    def get_ingestions(
        self, model_id: str, project_id: str
    ) -> ResourceCollection[Ingestion]:
        QUERY = gql(
            """
            query GetIngest($modelId: String!, $projectId: String!) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  data:ingests {
                    cursor
                    items {
                      createdAt
                      errorReason
                      errorStacktrace
                      fileName
                      id
                      maxIdleTimeoutMinutes
                      modelId
                      performanceData
                      progress
                      progressMessage
                      projectId
                      sourceApplication
                      sourceApplicationVersion
                      sourceFileData
                      status
                      updatedAt
                      versionId
                      user {
                        avatar
                        bio
                        company
                        id
                        name
                        role
                        verified
                      }
                    }
                  }
                }
              }
            }
            """
        )

        variables = {
            "modelId": model_id,
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ResourceCollection[Ingestion]]]],
            QUERY,
            variables,
        ).data.data.data

    def update(self, input: IngestUpdateInput) -> bool:
        QUERY = gql(
            """
            mutation IngestUpdate($projectId: ID!, $input: IngestUpdateInput!) {
              data: projectMutations {
                data: ingestMutations(projectId: $projectId) {
                  data: update(input: $input)
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
            "projectId": input.project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[bool]]],
            QUERY,
            variables,
        ).data.data.data

    def create(self, input: IngestCreateInput) -> Ingestion:
        QUERY = gql(
            """
            mutation IngestCreate($projectId: ID!, $input: IngestCreateInput!) {
              data: projectMutations {
                data:ingestMutations(projectId: $projectId) {
                  data:create(input: $input)  {
                    createdAt
                    errorReason
                    errorStacktrace
                    fileName
                    id
                    maxIdleTimeoutMinutes
                    modelId
                    performanceData
                    progress
                    progressMessage
                    projectId
                    sourceApplication
                    sourceApplicationVersion
                    sourceFileData
                    status
                    updatedAt
                    versionId
                    user {
                      avatar
                      bio
                      company
                      id
                      name
                      role
                      verified
                    }
                  }
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
            "projectId": input.project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[Ingestion]]],
            QUERY,
            variables,
        ).data.data.data

    def end(self, input: IngestFinishInput) -> Version:
        QUERY = gql(
            """
            mutation IngestEnd($projectId: ID!, $input: IngestFinishInput!) {
              data: projectMutations {
                data:ingestMutations(projectId: $projectId) {
                  data:end(input: $input) {
                    id
                    referencedObject
                    message
                    sourceApplication
                    createdAt
                    previewUrl
                    authorUser {
                      id
                      name
                      bio
                      company
                      verified
                      role
                      avatar
                    }
                  }
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
            "projectId": input.project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[Version]]],
            QUERY,
            variables,
        ).data.data.data

    def error(self, input: IngestErrorInput) -> bool:
        QUERY = gql(
            """
            mutation IngestError($projectId: ID!, $input: IngestErrorInput!) {
              data: projectMutations {
                data:ingestMutations(projectId: $projectId) {
                  data:error(input: $input)
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
            "projectId": input.project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[bool]]],
            QUERY,
            variables,
        ).data.data.data

    def cancel(self, input: CancelRequestInput) -> bool:
        QUERY = gql(
            """
            mutation IngestCancel($projectId: ID!, $input: CancelRequestInput!) {
              data:projectMutations {
                data:ingestMutations(projectId: $projectId) {
                  data:cancel(input: $input)
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
            "projectId": input.project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[bool]]],
            QUERY,
            variables,
        ).data.data.data
