from typing import Optional

from gql import gql

from specklepy.core.api.inputs.model_inputs import ModelVersionsFilter
from specklepy.core.api.inputs.version_inputs import (
    CreateVersionInput,
    DeleteVersionsInput,
    MarkReceivedVersionInput,
    MoveVersionsInput,
    UpdateVersionInput,
)
from specklepy.core.api.models import ResourceCollection, Version
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

NAME = "model"


class VersionResource(ResourceBase):
    """API Access class for model versions"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def get(self, version_id: str, project_id: str) -> Version:
        QUERY = gql(
            """
            query VersionGet($projectId: String!, $versionId: String!) {
              data:project(id: $projectId) {
                data:version(id: $versionId) {
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
            """
        )

        variables = {
            "projectId": project_id,
            "versionId": version_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Version]], QUERY, variables
        ).data.data

    def get_versions(
        self,
        model_id: str,
        project_id: str,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[ModelVersionsFilter] = None,
    ) -> ResourceCollection[Version]:
        QUERY = gql(
            """
            query VersionGetVersions($projectId: String!, $modelId: String!, $limit: Int!, $cursor: String, $filter: ModelVersionsFilter) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  data:versions(limit: $limit, cursor: $cursor, filter: $filter) {
                    items {
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
                    cursor
                    totalCount
                  }
                }
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
            "modelId": model_id,
            "limit": limit,
            "cursor": cursor,
            "filter": filter.model_dump(warnings="error") if filter else None,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ResourceCollection[Version]]]],
            QUERY,
            variables,
        ).data.data.data

    def create(self, input: CreateVersionInput) -> str:
        QUERY = gql(
            """
            mutation Create($input: CreateVersionInput!) {
              data:versionMutations {
                data:create(input: $input) {
                  data:id
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[str]]], QUERY, variables
        ).data.data.data

    def update(self, input: UpdateVersionInput) -> Version:
        QUERY = gql(
            """
            mutation VersionUpdate($input: UpdateVersionInput!) {
              data:versionMutations {
                data:update(input: $input) {
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
            """
        )

        variables = {"input": input.model_dump(warnings="error")}

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Version]], QUERY, variables
        ).data.data

    def move_to_model(self, input: MoveVersionsInput) -> str:
        QUERY = gql(
            """
            mutation VersionMoveToModel($input: MoveVersionsInput!) {
              data:versionMutations {
                data:moveToModel(input: $input) {
                  data:id
                }
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[str]]], QUERY, variables
        ).data.data.data

    def delete(self, input: DeleteVersionsInput) -> bool:
        QUERY = gql(
            """
            mutation VersionDelete($input: DeleteVersionsInput!) {
              data:versionMutations {
                data:delete(input: $input)
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], QUERY, variables
        ).data.data

    def received(self, input: MarkReceivedVersionInput) -> bool:
        QUERY = gql(
            """
            mutation MarkReceived($input: MarkReceivedVersionInput!) {
              data:versionMutations {
                data:markReceived(input: $input)
              }
            }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], QUERY, variables
        ).data.data
