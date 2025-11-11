import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.user_inputs import UserProjectsFilter
from specklepy.core.api.models.current import (
    Project,
    ProjectWithPermissions,
    ResourceCollection,
)


@pytest.mark.run()
class TestActiveUserResourcePermissions:
    @pytest.fixture()
    def test_project(self, client: SpeckleClient) -> Project:
        project = client.project.create(
            ProjectCreateInput(
                name="test project for active user permissions",
                description="test description",
                visibility=None,
            )
        )
        return project

    def test_active_user_get_projects_with_permissions(
        self, client: SpeckleClient, test_project: Project
    ):
        result = client.active_user.get_projects_with_permissions()

        assert isinstance(result, ResourceCollection)
        assert len(result.items) >= 1

        test_project_with_permissions = None
        for project in result.items:
            if project.id == test_project.id:
                test_project_with_permissions = project
                break

        assert test_project_with_permissions is not None
        assert isinstance(test_project_with_permissions, ProjectWithPermissions)

        assert hasattr(test_project_with_permissions, "permissions")
        assert test_project_with_permissions.permissions is not None

        assert test_project_with_permissions.id == test_project.id
        assert test_project_with_permissions.name == test_project.name

        permissions = test_project_with_permissions.permissions
        assert hasattr(permissions, "can_create_model")
        assert hasattr(permissions, "can_delete")
        assert hasattr(permissions, "can_load")
        assert hasattr(permissions, "can_publish")

        assert permissions.can_create_model.authorized is True
        assert permissions.can_delete.authorized is True
        assert permissions.can_load.authorized is True
        assert permissions.can_publish.authorized is True

    def test_active_user_get_projects_with_permissions_with_filter(
        self, client: SpeckleClient, test_project: Project
    ):
        """test getting active user's projects with permissions using a filter."""
        filter = UserProjectsFilter(search=test_project.name)

        result = client.active_user.get_projects_with_permissions(filter=filter)

        assert isinstance(result, ResourceCollection)
        assert len(result.items) >= 1
        assert result.total_count >= 1

        project_with_permissions = result.items[0]
        assert isinstance(project_with_permissions, ProjectWithPermissions)
        assert project_with_permissions.id == test_project.id

        assert hasattr(project_with_permissions, "permissions")
        assert project_with_permissions.permissions is not None

    def test_active_user_projects_with_permissions_method_exists(
        self, client: SpeckleClient
    ):
        """test that the method exists and is callable on active user resource."""
        assert hasattr(client.active_user, "get_projects_with_permissions")
        method = client.active_user.get_projects_with_permissions
        assert callable(method)
