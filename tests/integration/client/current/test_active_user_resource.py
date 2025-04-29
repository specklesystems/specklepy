import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.user_inputs import UserProjectsFilter, UserUpdateInput
from specklepy.core.api.models import ResourceCollection, User
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestActiveUserResource:
    def test_active_user_get(self, client: SpeckleClient):
        res = client.active_user.get()

        assert isinstance(res, User)

    def test_active_user_update(self, client: SpeckleClient):
        NEW_NAME = "Ron"
        NEW_BIO = "Now I have a bio, isn't that nice!"
        NEW_COMPANY = "Limited Cooperation Organization Inc"

        input = UserUpdateInput(name=NEW_NAME, bio=NEW_BIO, company=NEW_COMPANY)
        res = client.active_user.update(input=input)

        assert isinstance(res, User)
        assert res.name == NEW_NAME
        assert res.bio == NEW_BIO
        assert res.company == NEW_COMPANY

    def test_active_user_get_projects(self, client: SpeckleClient):
        existing = client.active_user.get_projects()

        p1 = client.project.create(
            ProjectCreateInput(name="Project 1", description=None, visibility=None)
        )
        p2 = client.project.create(
            ProjectCreateInput(name="Project 2", description=None, visibility=None)
        )

        res = client.active_user.get_projects()

        assert isinstance(res, ResourceCollection)
        assert len(res.items) == len(existing.items) + 2
        assert any(project.id == p1.id for project in res.items)
        assert any(project.id == p2.id for project in res.items)

    def test_active_user_get_projects_with_filter(self, client: SpeckleClient):
        # Since the client may be reused for other tests,
        # this test does rely on no other test creating a project
        # with "Search for me" in its name
        p1 = client.project.create(
            ProjectCreateInput(name="Search for me!", description=None, visibility=None)
        )
        _ = client.project.create(
            ProjectCreateInput(name="But not me!", description=None, visibility=None)
        )
        filter = UserProjectsFilter(search="Search for me")

        res = client.active_user.get_projects(filter=filter)

        assert isinstance(res, ResourceCollection)
        assert len(res.items) == 1
        assert res.total_count == 1
        assert res.items[0].id == p1.id

    def test_can_create_personal_projects(self, client: SpeckleClient):
        res = client.active_user.can_create_personal_projects()
        res.ensure_authorised()

        assert res.authorized is True

    def test_get_workspaces(self, client: SpeckleClient):
        """
        Test server is not workspace enabled, so we can't really test everything here
        We'll just test client's error handling
        """
        with pytest.raises(GraphQLException):
            _ = client.active_user.get_workspaces()

    def test_get_active_workspace(self, client: SpeckleClient):
        """
        Test server is not workspace enabled, so we can't really test everything here
        """
        res = client.active_user.get_active_workspace()
        assert res is None
