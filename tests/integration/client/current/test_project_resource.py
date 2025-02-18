import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectUpdateInput,
)
from specklepy.core.api.models import Project
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestProjectResource:
    @pytest.fixture()
    def test_project(self, client: SpeckleClient) -> Project:
        project = client.project.create(
            ProjectCreateInput(
                name="test project123",
                description="desc",
                visibility=ProjectVisibility.PRIVATE,
            )
        )
        return project

    @pytest.mark.parametrize(
        "name, description, visibility",
        [
            ("Very private project", "My secret project", ProjectVisibility.PRIVATE),
            ("Very public project", None, ProjectVisibility.PUBLIC),
        ],
    )
    def test_project_create(
        self,
        client: SpeckleClient,
        name: str,
        description: str,
        visibility: ProjectVisibility,
    ):
        input = ProjectCreateInput(
            name=name,
            description=description,
            visibility=visibility,
        )
        result = client.project.create(input)

        assert isinstance(result, Project)
        assert result.id is not None
        assert result.name == name
        assert result.description == (description or "")
        assert result.visibility == visibility

    def test_project_get(self, client: SpeckleClient, test_project: Project):
        result = client.project.get(test_project.id)

        assert isinstance(result, Project)
        assert result.id == test_project.id
        assert result.name == test_project.name
        assert result.description == test_project.description
        assert result.visibility == test_project.visibility
        assert result.created_at == test_project.created_at

    def test_project_update(self, client: SpeckleClient, test_project: Project):
        new_name = "MY new name"
        new_description = "MY new desc"
        new_visibility = ProjectVisibility.PUBLIC

        update_data = ProjectUpdateInput(
            id=test_project.id,
            name=new_name,
            description=new_description,
            visibility=new_visibility,
        )

        updated_project = client.project.update(update_data)

        assert isinstance(updated_project, Project)
        assert updated_project.id == test_project.id
        assert updated_project.name == new_name
        assert updated_project.description == new_description
        assert updated_project.visibility == new_visibility

    def test_project_delete(self, client: SpeckleClient):
        """Test deleting a project."""
        project_to_delete = client.project.create(
            ProjectCreateInput(name="Delete me", description=None, visibility=None)
        )

        response = client.project.delete(project_to_delete.id)
        assert response is True

        with pytest.raises(GraphQLException):
            client.project.get(project_to_delete.id)
