from typing import Callable, Optional, Sequence

from deprecated import deprecated
from pydantic import BaseModel
from typing_extensions import TypeVar

from specklepy.core.api.models import FE1_DEPRECATION_REASON, FE1_DEPRECATION_VERSION
from specklepy.core.api.new_models import (
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
)
from specklepy.core.api.resources.subscription_resource import (
    SubscriptionResource as CoreResource,
)
from specklepy.core.api.resources.subscription_resource import check_wsclient
from specklepy.logging import metrics

TEventArgs = TypeVar("TEventArgs", bound=BaseModel)


class SubscriptionResource(CoreResource):
    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
        )

    async def user_projects_updated(
        self, callback: Callable[[UserProjectsUpdatedMessage], None]
    ) -> None:
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Project Models Updated"}
        )
        return await super().user_projects_updated(callback)

    async def project_models_updated(
        self,
        callback: Callable[[ProjectModelsUpdatedMessage], None],
        id: str,
        *,
        model_ids: Optional[Sequence[str]] = None,
    ) -> None:
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Project Models Updated"}
        )
        return await super().project_models_updated(callback, id, model_ids=model_ids)

    async def project_updated(
        self,
        callback: Callable[[ProjectUpdatedMessage], None],
        id: str,
    ) -> None:
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Project Updated"}
        )
        return await super().project_updated(callback, id)

    async def project_versions_updated(
        self,
        callback: Callable[[ProjectVersionsUpdatedMessage], None],
        id: str,
    ) -> None:
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Project Versions Updated"}
        )
        return await super().project_versions_updated(callback, id)

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
        metrics.track(metrics.SDK, self.account, {"name": "Subscription Stream Added"})
        return super().stream_added(callback)

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
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Stream Updated"}
        )
        return super().stream_updated(id, callback)

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
        metrics.track(
            metrics.SDK, self.account, {"name": "Subscription Stream Removed"}
        )
        return super().stream_removed(callback)
