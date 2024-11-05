from typing import Any, Optional, Tuple

from gql import Client

from specklepy.core.api.credentials import Account
from specklepy.core.api.inputs.project_inputs import (
    ProjectInviteCreateInput,
    ProjectInviteUseInput,
)
from specklepy.core.api.models import PendingStreamCollaborator, ProjectWithTeam
from specklepy.core.api.resources import ProjectInviteResource as CoreResource
from specklepy.logging import metrics


class ProjectInviteResource(CoreResource):
    """API Access class for project invites"""

    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        server_version: Optional[Tuple[Any, ...]],
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

    def create(
        self, project_id: str, input: ProjectInviteCreateInput
    ) -> ProjectWithTeam:
        metrics.track(metrics.SDK, self.account, {"name": "Project Invite Create"})
        return super().create(project_id, input)

    def use(self, input: ProjectInviteUseInput) -> bool:
        metrics.track(metrics.SDK, self.account, {"name": "Project Invite Use"})
        return super().use(input)

    def get(
        self, project_id: str, token: Optional[str]
    ) -> Optional[PendingStreamCollaborator]:
        metrics.track(metrics.SDK, self.account, {"name": "Project Invite Get"})
        return super().get(project_id, token)

    def cancel(
        self,
        project_id: str,
        invite_id: str,
    ) -> ProjectWithTeam:
        metrics.track(metrics.SDK, self.account, {"name": "Project Invite Cancel"})
        return super().cancel(project_id, invite_id)
