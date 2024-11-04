from typing import Optional

from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectModelsFilter,
    ProjectUpdateInput,
    ProjectUpdateRoleInput,
)
from specklepy.core.api.models import Project, ProjectWithModels, ProjectWithTeam
from specklepy.core.api.resources import ProjectResource as CoreResource
from specklepy.logging import metrics


class ProjectResource(CoreResource):
    """API Access class for projects"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

    def get(self, project_id: str) -> Project:
        metrics.track(metrics.SDK, self.account, {"name": "Project Get "})
        return super().get(project_id)

    def get_with_models(
        self,
        project_id: str,
        *,
        models_limit: int = 25,
        models_cursor: Optional[str] = None,
        models_filter: Optional[ProjectModelsFilter] = None,
    ) -> ProjectWithModels:
        metrics.track(metrics.SDK, self.account, {"name": "Project Get With Models"})
        return super().get_with_models(
            project_id,
            models_limit=models_limit,
            models_cursor=models_cursor,
            models_filter=models_filter,
        )

    def get_with_team(self, project_id: str) -> ProjectWithTeam:
        metrics.track(metrics.SDK, self.account, {"name": "Project Get With Team"})
        return super().get_with_team(project_id)

    def create(self, input: ProjectCreateInput) -> Project:
        metrics.track(metrics.SDK, self.account, {"name": "Project Create"})
        return super().create(input)

    def update(self, input: ProjectUpdateInput) -> Project:
        metrics.track(metrics.SDK, self.account, {"name": "Project Update"})
        return super().update(input)

    def delete(self, project_id: str) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Project Delete"})
        return super().delete(project_id)

    def update_role(self, input: ProjectUpdateRoleInput) -> ProjectWithTeam:
        metrics.track(metrics.SDK, self.account, {"name": "Project Update Role"})
        return super().update_role(input)
