from typing import Optional

from specklepy.core.api.inputs.project_inputs import WorksaceProjectsFilter
from specklepy.core.api.models.current import Project, ResourceCollection, Workspace
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

    def get_projects(
        self,
        workspace_id: str,
        limit: int = 25,
        cursor: Optional[str] = None,
        filter: Optional[WorksaceProjectsFilter] = None,
    ) -> ResourceCollection[Project]:
        metrics.track(metrics.SDK, self.account, {"name": "Workspace Get Projects"})
        return super().get_projects(workspace_id, limit, cursor, filter)
