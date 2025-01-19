from functools import wraps
from typing import Callable, Dict, List, Optional, Union

from deprecated import deprecated
from gql import gql
from graphql import DocumentNode

from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
    Stream,
)
from specklepy.core.api.resource import ResourceBase
from specklepy.logging.exceptions import SpeckleException

NAME = "subscribe"


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


class Resource(ResourceBase):
    """API Access class for subscriptions"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
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
