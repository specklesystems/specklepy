from gql import gql

from specklepy.api.inputs.model_inputs import ModelVersionsFilter
from specklepy.api.inputs.version_inputs import (
    CreateVersionInput,
    DeleteVersionsInput,
    MarkReceivedVersionInput,
    MoveVersionsInput,
    UpdateVersionInput,
)
from specklepy.api.models import ResourceCollection, Version
from specklepy.api.resource import ResourceBase
from specklepy.api.responses import DataResponse

NAME = "version"


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
        request = gql(
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

        request.variable_values = {
            "projectId": project_id,
            "versionId": version_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Version]], request
        ).data.data

    def get_versions(
        self,
        model_id: str,
        project_id: str,
        *,
        limit: int = 25,
        cursor: str | None = None,
        filter: ModelVersionsFilter | None = None,
    ) -> ResourceCollection[Version]:
        request = gql(
            """
            query VersionGetVersions(
              $projectId: String!,
              $modelId: String!,
              $limit: Int!,
              $cursor: String,
              $filter: ModelVersionsFilter
              ) {
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

        request.variable_values = {
            "projectId": project_id,
            "modelId": model_id,
            "limit": limit,
            "cursor": cursor,
            "filter": (
                filter.model_dump(warnings="error", by_alias=True) if filter else None
            ),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ResourceCollection[Version]]]],
            request,
        ).data.data.data

    def create(self, input: CreateVersionInput) -> Version:
        request = gql(
            """
            mutation Create($input: CreateVersionInput!) {
              data:versionMutations {
                data:create(input: $input) {
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
        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Version]], request
        ).data.data

    def update(self, input: UpdateVersionInput) -> Version:
        request = gql(
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

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True)
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Version]], request
        ).data.data

    def move_to_model(self, input: MoveVersionsInput) -> str:
        request = gql(
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

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[str]]], request
        ).data.data.data

    def delete(self, input: DeleteVersionsInput) -> bool:
        request = gql(
            """
            mutation VersionDelete($input: DeleteVersionsInput!) {
              data:versionMutations {
                data:delete(input: $input)
              }
            }
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], request
        ).data.data

    def received(self, input: MarkReceivedVersionInput) -> bool:
        request = gql(
            """
            mutation MarkReceived($input: MarkReceivedVersionInput!) {
              data:versionMutations {
                data:markReceived(input: $input)
              }
            }
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], request
        ).data.data
