from gql import gql

from specklepy.api.inputs.model_inputs import (
    CreateModelInput,
    DeleteModelInput,
    ModelVersionsFilter,
    UpdateModelInput,
)
from specklepy.api.inputs.project_inputs import ProjectModelsFilter
from specklepy.api.models import Model, ModelWithVersions, ResourceCollection
from specklepy.api.models.current import (
    ModelPermissionChecks,
    PermissionCheckResult,
)
from specklepy.api.resource import ResourceBase
from specklepy.api.responses import DataResponse

NAME = "model"


class ModelResource(ResourceBase):
    """API Access class for models"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
            server_version=server_version,
        )

    def get(self, model_id: str, project_id: str) -> Model:
        request = gql(
            """
            query ModelGet($modelId: String!, $projectId: String!) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  id
                  name
                  previewUrl
                  updatedAt
                  description
                  displayName
                  createdAt
                  author {
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
            """
        )

        request.variable_values = {
            "modelId": model_id,
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], request
        ).data.data

    def get_with_versions(
        self,
        model_id: str,
        project_id: str,
        *,
        versions_limit: int = 25,
        versions_cursor: str | None = None,
        versions_filter: ModelVersionsFilter | None = None,
    ) -> ModelWithVersions:
        request = gql(
            """
            query ModelGetWithVersions(
              $modelId: String!,
              $projectId: String!,
              $versionsLimit: Int!,
              $versionsCursor: String,
              $versionsFilter: ModelVersionsFilter
              ) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  id
                  name
                  previewUrl
                  updatedAt
                  versions(
                    limit: $versionsLimit,
                    cursor: $versionsCursor,
                    filter: $versionsFilter
                    ) {
                    items {
                      id
                      referencedObject
                      message
                      sourceApplication
                      createdAt
                      previewUrl
                      authorUser {
                        avatar
                        id
                        name
                        bio
                        company
                        verified
                        role
                      }
                    }
                    totalCount
                    cursor
                  }
                  description
                  displayName
                  createdAt
                  author {
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
            """
        )

        request.variable_values = {
            "projectId": project_id,
            "modelId": model_id,
            "versionsLimit": versions_limit,
            "versionsCursor": versions_cursor,
            "versionsFilter": (
                versions_filter.model_dump(warnings="error", by_alias=True)
                if versions_filter
                else None
            ),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ModelWithVersions]], request
        ).data.data

    def get_models(
        self,
        project_id: str,
        *,
        models_limit: int = 25,
        models_cursor: str | None = None,
        models_filter: ProjectModelsFilter | None = None,
    ) -> ResourceCollection[Model]:
        request = gql(
            """
            query ProjectGetWithModels(
              $projectId: String!,
              $modelsLimit: Int!,
              $modelsCursor: String,
              $modelsFilter: ProjectModelsFilter
              ) {
              data:project(id: $projectId) {
                data:models(
                  limit: $modelsLimit,
                  cursor: $modelsCursor,
                  filter: $modelsFilter
                  ) {
                  items {
                    id
                    name
                    previewUrl
                    updatedAt
                    displayName
                    description
                    createdAt
                    author {
                      avatar
                      bio
                      company
                      id
                      name
                      role
                      verified
                    }
                  }
                  totalCount
                  cursor
                }
              }
            }
            """
        )

        request.variable_values = {
            "projectId": project_id,
            "modelsLimit": models_limit,
            "modelsCursor": models_cursor,
            "modelsFilter": (
                models_filter.model_dump(warnings="error", by_alias=True)
                if models_filter
                else None
            ),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ResourceCollection[Model]]], request
        ).data.data

    def create(self, input: CreateModelInput) -> Model:
        request = gql(
            """
            mutation ModelCreate($input: CreateModelInput!) {
              data:modelMutations {
                data:create(input: $input) {
                  id
                  displayName
                  name
                  description
                  createdAt
                  updatedAt
                  previewUrl
                  author {
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
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], request
        ).data.data

    def delete(self, input: DeleteModelInput) -> bool:
        request = gql(
            """
            mutation ModelDelete($input: DeleteModelInput!) {
              data:modelMutations {
                data:delete(input: $input)
              }
            }
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True)
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], request
        ).data.data

    def update(self, input: UpdateModelInput) -> Model:
        request = gql(
            """
            mutation ModelUpdate($input: UpdateModelInput!) {
              data:modelMutations {
                data:update(input: $input) {
                  id
                  name
                  displayName
                  description
                  createdAt
                  updatedAt
                  previewUrl
                  author {
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
            """
        )

        request.variable_values = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], request
        ).data.data

    def get_permissions(self, project_id: str, model_id: str) -> ModelPermissionChecks:
        request = gql(
            """
            query ModelPermissions($projectId: String!, $modelId: String!) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  data:permissions {
                    canUpdate {
                      authorized
                      code
                      message
                    }
                    canDelete {
                      authorized
                      code
                      message
                    }
                    canCreateVersion {
                      authorized
                      code
                      message
                    }
                  }
                }
              }
            }
            """
        )

        request.variable_values = {"projectId": project_id, "modelId": model_id}

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ModelPermissionChecks]]],
            request,
        ).data.data.data

    def can_create_model_ingestion(
        self, project_id: str, model_id: str
    ) -> PermissionCheckResult:
        request = gql(
            """
            query ModelPermissions($projectId: String!, $modelId: String!) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  data:permissions {
                    data:canCreateIngestion {
                      authorized
                      code
                      message
                    }
                  }
                }
              }
            }
            """
        )

        request.variable_values = {"projectId": project_id, "modelId": model_id}

        return self.make_request_and_parse_response(
            DataResponse[
                DataResponse[DataResponse[DataResponse[PermissionCheckResult]]]
            ],
            request,
        ).data.data.data.data
