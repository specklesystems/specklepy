from specklepy.core.api.models.current import Workspace
from specklepy.core.api.resources import WorkspaceResource as CoreResource
from specklepy.logging import metrics


class WorkspaceResource(CoreResource):
    """API Access class for workspace"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

    def get(self, workspace_id: str) -> Workspace:
        metrics.track(metrics.SDK, self.account, {"name": "Workspace Get"})
        return super().get(workspace_id)
