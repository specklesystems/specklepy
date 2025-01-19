from typing import Callable, Optional, Sequence

from pydantic import BaseModel
from typing_extensions import TypeVar

from specklepy.core.api.models import (
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
)
from specklepy.core.api.resources import SubscriptionResource as CoreResource
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
