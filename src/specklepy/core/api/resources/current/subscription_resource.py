from functools import wraps
from typing import Any, Callable, Dict, Optional, Sequence, Type

from gql import gql
from graphql import DocumentNode
from pydantic import BaseModel
from typing_extensions import TypeVar

from specklepy.core.api.enums import ProjectModelIngestionUpdatedMessageType
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionReference,
    ProjectModelIngestionSubscriptionInput,
)
from specklepy.core.api.models import (
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
)
from specklepy.core.api.models.subscription_messages import (
    ProjectModelIngestionUpdatedMessage,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import SpeckleException

NAME = "subscription"

TEventArgs = TypeVar("TEventArgs", bound=BaseModel)


def check_wsclient(function):
    @wraps(function)
    async def check_wsclient_wrapper(self, *args, **kwargs):
        if self.client is None:
            raise SpeckleException(
                "You must authenticate before you can subscribe to events"
            )
        else:
            return await function(self, *args, **kwargs)

    return check_wsclient_wrapper


class SubscriptionResource(ResourceBase):
    """API Access class for subscriptions"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
        )

    async def user_projects_updated(
        self, callback: Callable[[UserProjectsUpdatedMessage], None]
    ) -> None:
        QUERY = gql(
            """
            subscription UserProjectsUpdated {
              data:userProjectsUpdated {
                id
                project {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  sourceApps
                  workspaceId
                }
                type
              }
            }
            """
        )

        await self.subscribe_2(
            DataResponse[UserProjectsUpdatedMessage],
            QUERY,
            None,
            callback=lambda d: callback(d.data),
        )

    async def project_models_updated(
        self,
        callback: Callable[[ProjectModelsUpdatedMessage], None],
        id: str,
        model_ids: Optional[Sequence[str]] = None,
    ) -> None:
        QUERY = gql(
            """
            subscription ProjectModelsUpdated($id: String!, $modelIds: [String!]) {
              data:projectModelsUpdated(id: $id, modelIds: $modelIds) {
                id
                model {
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
                type
              }
            }
            """
        )

        variables = {"id": id, "modelIds": model_ids}

        await self.subscribe_2(
            DataResponse[ProjectModelsUpdatedMessage],
            QUERY,
            variables,
            callback=lambda d: callback(d.data),
        )

    async def project_updated(
        self,
        callback: Callable[[ProjectUpdatedMessage], None],
        id: str,
    ) -> None:
        QUERY = gql(
            """
            subscription ProjectUpdated($id: String!) {
              data:projectUpdated(id: $id) {
                id
                project {
                  id
                  name
                  description
                  visibility
                  allowPublicComments
                  role
                  createdAt
                  updatedAt
                  sourceApps
                  workspaceId
                }
                type
              }
            }
            """
        )

        variables = {"id": id}

        await self.subscribe_2(
            DataResponse[ProjectUpdatedMessage],
            QUERY,
            variables,
            callback=lambda d: callback(d.data),
        )

    async def project_versions_updated(
        self,
        callback: Callable[[ProjectVersionsUpdatedMessage], None],
        id: str,
    ) -> None:
        QUERY = gql(
            """
            subscription ProjectVersionsUpdated($id: String!) {
              data:projectVersionsUpdated(id: $id) {
                id
                modelId
                type
                version {
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

        variables = {"id": id}

        await self.subscribe_2(
            DataResponse[ProjectVersionsUpdatedMessage],
            QUERY,
            variables,
            callback=lambda d: callback(d.data),
        )

    async def project_model_ingestion_updated(
        self,
        callback: Callable[[ProjectModelIngestionUpdatedMessage], None],
        input: ProjectModelIngestionSubscriptionInput,
    ) -> None:
        QUERY = gql(
            """
            subscription IngestionUpdated($input: ProjectModelIngestionSubscriptionInput!) {
              data: projectModelIngestionUpdated(input: $input) {
                modelIngestion {
                  id
                  createdAt
                  updatedAt
                  modelId
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
                type
              }
            }
            """  # noqa: E501
        )

        variables = {
            "input": input.model_dump(
                warnings="error", by_alias=True, exclude_none=True
            ),
        }

        await self.subscribe_2(
            DataResponse[ProjectModelIngestionUpdatedMessage],
            QUERY,
            variables,
            callback=lambda d: callback(d.data),
        )

    async def project_model_ingestion_cancellation_requested(
        self,
        callback: Callable[[ProjectModelIngestionUpdatedMessage], None],
        project_id: str,
        ingestion_id: str,
    ) -> None:
        await self.project_model_ingestion_updated(
            callback,
            ProjectModelIngestionSubscriptionInput(
                project_id=project_id,
                ingestion_reference=ModelIngestionReference(
                    ingestion_id=ingestion_id, model_id=None
                ),
                message_type=ProjectModelIngestionUpdatedMessageType.CANCELLATION_REQUESTED,
            ),
        )

    @check_wsclient
    async def subscribe_2(
        self,
        response_type: Type[TEventArgs],
        query: DocumentNode,
        variables: Optional[Dict[str, Any]],
        callback: Callable[[TEventArgs], None],
    ) -> None:
        async with self.client as session:
            self.session = session
            gen = session.subscribe(query, variable_values=variables)
            async for res in gen:
                event_arg = response_type.model_validate(res)
                callback(event_arg)
