from typing import Optional

from gql import gql

from specklepy.core.api.inputs.model_inputs import (
    CreateModelInput,
    DeleteModelInput,
    ModelVersionsFilter,
    UpdateModelInput,
)
from specklepy.core.api.inputs.project_inputs import ProjectModelsFilter
from specklepy.core.api.models import Model, ModelWithVersions, ResourceCollection
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse

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
        QUERY = gql(
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

        variables = {
            "modelId": model_id,
            "projectId": project_id,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], QUERY, variables
        ).data.data

    def get_with_versions(
        self,
        model_id: str,
        project_id: str,
        *,
        versions_limit: int = 25,
        versions_cursor: Optional[str] = None,
        versions_filter: Optional[ModelVersionsFilter] = None,
    ) -> ModelWithVersions:
        QUERY = gql(
            """
            query ModelGetWithVersions($modelId: String!, $projectId: String!, $versionsLimit: Int!, $versionsCursor: String, $versionsFilter: ModelVersionsFilter) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                  id
                  name
                  previewUrl
                  updatedAt
                  versions(limit: $versionsLimit, cursor: $versionsCursor, filter: $versionsFilter) {
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

        variables = {
            "projectId": project_id,
            "modelId": model_id,
            "versionsLimit": versions_limit,
            "versionsCursor": versions_cursor,
            "versionsFilter": versions_filter.model_dump(warnings="error")
            if versions_filter
            else None,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ModelWithVersions]], QUERY, variables
        ).data.data

    def get_models(
        self,
        project_id: str,
        *,
        models_limit: int = 25,
        models_cursor: Optional[str] = None,
        models_filter: Optional[ProjectModelsFilter] = None,
    ) -> ResourceCollection[Model]:
        QUERY = gql(
            """
            query ProjectGetWithModels($projectId: String!, $modelsLimit: Int!, $modelsCursor: String, $modelsFilter: ProjectModelsFilter) {
              data:project(id: $projectId) {
                data:models(limit: $modelsLimit, cursor: $modelsCursor, filter: $modelsFilter) {
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

        variables = {
            "projectId": project_id,
            "modelsLimit": models_limit,
            "modelsCursor": models_cursor,
            "modelsFilter": models_filter.model_dump(warnings="error")
            if models_filter
            else None,
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[ResourceCollection[Model]]], QUERY, variables
        ).data.data

    def create(self, input: CreateModelInput) -> Model:
        QUERY = gql(
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

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], QUERY, variables
        ).data.data

    def delete(self, input: DeleteModelInput) -> bool:
        QUERY = gql(
            """
            mutation ModelDelete($input: DeleteModelInput!) {
              data:modelMutations {
                data:delete(input: $input)
              }
            }
            """
        )

        variables = {"input": input.model_dump(warnings="error")}

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], QUERY, variables
        ).data.data

    def update(self, input: UpdateModelInput) -> Model:
        QUERY = gql(
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

        variables = {
            "input": input.model_dump(warnings="error"),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[Model]], QUERY, variables
        ).data.data
