from typing import Optional

from specklepy.core.api.inputs.model_inputs import ModelVersionsFilter
from specklepy.core.api.inputs.version_inputs import (
    CreateVersionInput,
    DeleteVersionsInput,
    MarkReceivedVersionInput,
    MoveVersionsInput,
    UpdateVersionInput,
)
from specklepy.core.api.models import ResourceCollection, Version
from specklepy.core.api.resources import VersionResource as CoreResource
from specklepy.logging import metrics


class VersionResource(CoreResource):
    """API Access class for model versions"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

    def get(self, version_id: str, project_id: str) -> Version:
        metrics.track(metrics.SDK, self.account, {"name": "Version Get"})
        return super().get(version_id, project_id)

    def get_versions(
        self,
        model_id: str,
        project_id: str,
        *,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[ModelVersionsFilter] = None,
    ) -> ResourceCollection[Version]:
        metrics.track(metrics.SDK, self.account, {"name": "Version Get Versions"})
        return super().get_versions(
            model_id, project_id, limit=limit, cursor=cursor, filter=filter
        )

    def create(self, input: CreateVersionInput) -> str:
        metrics.track(metrics.SDK, self.account, {"name": "Version Create"})
        return super().create(input)

    def update(self, input: UpdateVersionInput) -> Version:
        metrics.track(metrics.SDK, self.account, {"name": "Version Update"})
        return super().update(input)

    def move_to_model(self, input: MoveVersionsInput) -> str:
        metrics.track(metrics.SDK, self.account, {"name": "Version Move To Model"})
        return super().move_to_model(input)

    def delete(self, input: DeleteVersionsInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Version Delete"})
        return super().delete(input)

    def received(self, input: MarkReceivedVersionInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Version Received"})
        return super().received(input)
