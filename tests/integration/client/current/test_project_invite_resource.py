from typing import Optional

import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectInviteCreateInput,
    ProjectInviteUseInput,
    ProjectUpdateRoleInput,
)
from specklepy.core.api.models import (
    LimitedUser,
    PendingStreamCollaborator,
    Project,
    ProjectWithTeam,
)


@pytest.mark.run()
class TestProjectInviteResource:
    @pytest.fixture
    def project(self, client: SpeckleClient):
        return client.project.create(
            ProjectCreateInput(
                name="test", description=None, visibility=ProjectVisibility.PUBLIC
            )
        )

    @pytest.fixture
    def created_invite(
        self, client: SpeckleClient, second_client: SpeckleClient, project: Project
    ):
        input = ProjectInviteCreateInput(
            email=second_client.account.userInfo.email,
            role=None,
            server_role=None,
            userId=None,
        )
        res = client.project_invite.create(project.id, input)
        invites = second_client.active_user.get_project_invites()
        return next(i for i in invites if i.projectId == res.id)

    def test_project_invite_create_by_email(
        self, client: SpeckleClient, second_client: SpeckleClient, project: Project
    ):
        input = ProjectInviteCreateInput(
            email=second_client.account.userInfo.email,
            role=None,
            server_role=None,
            userId=None,
        )
        res = client.project_invite.create(project.id, input)

        invites = second_client.active_user.get_project_invites()
        invite = next(i for i in invites if i.projectId == res.id)

        assert isinstance(res, ProjectWithTeam)
        assert res.id == project.id
        assert len(res.invited_team) == 1

        assert isinstance(invite.user, LimitedUser)
        assert invite.user.id == second_client.account.userInfo.id
        assert invite.token

    def test_project_invite_create_by_user_id(
        self, client: SpeckleClient, second_client: SpeckleClient, project: Project
    ):
        input = ProjectInviteCreateInput(
            email=None,
            role=None,
            server_role=None,
            userId=second_client.account.userInfo.id,
        )
        res = client.project_invite.create(project.id, input)

        assert isinstance(res, ProjectWithTeam)
        assert res.id == project.id
        assert len(res.invited_team) == 1
        invited_team_member = res.invited_team[0].user
        assert isinstance(invited_team_member, LimitedUser)
        assert invited_team_member.id == second_client.account.userInfo.id

    def test_project_invite_get(
        self,
        second_client: SpeckleClient,
        project: Project,
        created_invite: PendingStreamCollaborator,
    ):
        collaborator = second_client.project_invite.get(
            project.id, created_invite.token
        )
        assert isinstance(collaborator, PendingStreamCollaborator)
        assert collaborator.invite_id == created_invite.invite_id

        assert isinstance(collaborator.user, LimitedUser)
        assert isinstance(created_invite.user, LimitedUser)

        assert collaborator.user.id == created_invite.user.id

    def test_project_invite_get_non_existing(
        self, second_client: SpeckleClient, project: Project
    ):
        collaborator = second_client.project_invite.get(
            project.id, "this is not a real token"
        )

        assert collaborator is None

    def test_project_invite_use_member_added(
        self,
        client: SpeckleClient,
        second_client: SpeckleClient,
        project: Project,
        created_invite: PendingStreamCollaborator,
    ):
        assert created_invite.token

        input = ProjectInviteUseInput(
            accept=True, project_id=created_invite.projectId, token=created_invite.token
        )
        res = second_client.project_invite.use(input)

        assert res is True

        project = client.project.get_with_team(project.id)
        assert isinstance(project, ProjectWithTeam)

        team_members = [c.user.id for c in project.team]
        expected_team_members = [
            client.account.userInfo.id,
            second_client.account.userInfo.id,
        ]

        assert set(team_members) == set(expected_team_members)

    def test_project_invite_cancel_member_not_added(
        self, client: SpeckleClient, created_invite: PendingStreamCollaborator
    ):
        res = client.project_invite.cancel(
            created_invite.projectId, created_invite.invite_id
        )

        assert isinstance(res, ProjectWithTeam)
        assert len(res.invited_team) == 0

    @pytest.mark.parametrize(
        "new_role", ["stream:owner", "stream:contributor", "stream:reviewer", None]
    )
    def test_project_update_role(
        self,
        client: SpeckleClient,
        second_client: SpeckleClient,
        project: Project,
        new_role: Optional[str],
        created_invite: PendingStreamCollaborator,
    ):
        assert created_invite.token

        input = ProjectInviteUseInput(
            accept=True, project_id=created_invite.projectId, token=created_invite.token
        )
        res = second_client.project_invite.use(input)

        invitee_id = second_client.account.userInfo.id
        assert invitee_id
        input = ProjectUpdateRoleInput(
            user_id=invitee_id,
            project_id=project.id,
            role=new_role,
        )
        res = client.project.update_role(input)

        assert isinstance(res, ProjectWithTeam)
        final_project = second_client.project.get(project.id)

        assert isinstance(res, Project)
        assert final_project.role == new_role
