from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union

from deprecated import deprecated
from gql import gql
from graphql import DocumentNode
from pydantic import BaseModel
from typing_extensions import TypeVar

from specklepy.core.api.models import FE1_DEPRECATION_REASON, FE1_DEPRECATION_VERSION
from specklepy.core.api.new_models import (
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.resources.stream import Stream
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import SpeckleException

NAME = "subscribe"

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

    @check_wsclient
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

    @check_wsclient
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

    @check_wsclient
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

    @check_wsclient
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

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    @check_wsclient
    async def stream_added(self, callback: Optional[Callable] = None):
        """Subscribes to new stream added event for your profile.
        Use this to display an up-to-date list of streams.

        Arguments:
            callback {Callable[Stream]} -- a function that takes the updated stream
            as an argument and executes each time a stream is added

        Returns:
            Stream -- the update stream
        """
        query = gql(
            """
            subscription { userStreamAdded }
            """
        )
        return await self.subscribe(
            query=query, callback=callback, return_type="userStreamAdded", schema=Stream
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    @check_wsclient
    async def stream_updated(self, id: str, callback: Optional[Callable] = None):
        """
        Subscribes to stream updated event.
        Use this in clients/components that pertain only to this stream.

        Arguments:
            id {str} -- the stream id of the stream to subscribe to
            callback {Callable[Stream]}
            -- a function that takes the updated stream
            as an argument and executes each time the stream is updated

        Returns:
            Stream -- the update stream
        """
        query = gql(
            """
            subscription Update($id: String!) { streamUpdated(streamId: $id) }
            """
        )
        params = {"id": id}

        return await self.subscribe(
            query=query,
            params=params,
            callback=callback,
            return_type="streamUpdated",
            schema=Stream,
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    @check_wsclient
    async def stream_removed(self, callback: Optional[Callable] = None):
        """Subscribes to stream removed event for your profile.
        Use this to display an up-to-date list of streams for your profile.
        NOTE: If someone revokes your permissions on a stream,
        this subscription will be triggered with an extra value of revokedBy
        in the payload.

        Arguments:
            callback {Callable[Dict]}
            -- a function that takes the returned dict as an argument
            and executes each time a stream is removed

        Returns:
            dict -- dict containing 'id' of stream removed and optionally 'revokedBy'
        """
        query = gql(
            """
            subscription { userStreamRemoved }
            """
        )

        return await self.subscribe(
            query=query,
            callback=callback,
            return_type="userStreamRemoved",
            parse_response=False,
        )

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    @check_wsclient
    async def subscribe(
        self,
        query: DocumentNode,
        params: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        return_type: Optional[Union[str, List]] = None,
        schema=None,
        parse_response: bool = True,
    ):
        # if self.client.transport.websocket is None:
        # TODO: add multiple subs to the same ws connection
        async with self.client as session:
            async for res in session.subscribe(query, variable_values=params):
                res = self._step_into_response(response=res, return_type=return_type)
                if parse_response:
                    res = self._parse_response(response=res, schema=schema)
                if callback is not None:
                    callback(res)
                else:
                    return res

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
