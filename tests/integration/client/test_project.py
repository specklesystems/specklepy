import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.models import (
    Project,
)
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectUpdateInput,
)
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run(order=3)
class TestProject:
    @pytest.fixture(scope="session")
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
        input_data = ProjectCreateInput(
            name=name,
            description=description,
            visibility=visibility,
        )
        result = client.project.create(input_data)

        assert result is not None
        assert result.id is not None
        assert result.name == name
        assert result.description == (description or "")
        assert result.visibility == visibility

    def test_project_get(self, client: SpeckleClient, test_project: Project):
        result = client.project.get(test_project.id)

        assert result.id == test_project.id
        assert result.name == test_project.name
        assert result.description == test_project.description
        assert result.visibility == test_project.visibility
        assert result.createdAt == test_project.createdAt

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

    # @pytest.fixture(scope="session")
    # def (self) -> Project:
    #     return Project(
    #         id= "TO BE SET LATER",
    #         name="a wonderful project",
    #         description="a project created for testing",
    #         visibility=ProjectVisibility.PUBLIC,
    #         allowPublicComments=false,
    #         createdAt=None,
    #         sourceApps=[]

    #     )

    # @pytest.fixture(scope="module")
    # def updated_project(
    #     self,
    # ) -> Project:
    #     return Project(
    #         name="a wonderful updated project",
    #         description="an updated project description for testing",
    #         visibility=ProjectVisibility.PRIVATE,
    #     )

    # def test_project_create(
    #     self, client: SpeckleClient, project: Project, updated_project: Project
    # ):
    #     result = client.project.create(
    #         ProjectCreateInput(
    #             name=project.name,
    #             description=project.description,
    #             visibility=project.visibility,
    #         )
    #     )

    #     assert isinstance(result.id, str)
    #     assert result.name == project.name
    #     assert result.description == project.description
    #     assert result.visibility == project.visibility

    #     project = updated_project = result

    #     _ = updated_project  # check if this actually is needed, are we mutating the right instance

    # def test_project_create_short_name(
    #     self, client: SpeckleClient, project: Project, updated_project: Project
    # ):
    #     new_project_id = client.project.create(
    #         ProjectCreateInput(
    #             name="x",
    #             description=project.description,
    #             visibility=project.visibility,
    #         )
    #     )
    #     assert isinstance(new_project_id, SpeckleException)

    # def test_project_get(self, client: SpeckleClient, project: Project):
    #     result = client.project.get(project.id)

    #     assert result.id == project.id
    #     assert result.name == project.name
    #     assert result.description == project.description
    #     assert result.visibility == project.visibility
    #     assert result.createdAt == project.createdAt

    # def test_stream_update(self, client, updated_stream):
    #     updated = client.stream.update(
    #         id=updated_stream.id,
    #         name=updated_stream.name,
    #         description=updated_stream.description,
    #         is_public=updated_stream.isPublic,
    #     )
    #     fetched_stream = client.stream.get(updated_stream.id)

    #     assert updated is True
    #     assert fetched_stream.name == updated_stream.name
    #     assert fetched_stream.description == updated_stream.description
    #     assert fetched_stream.isPublic == updated_stream.isPublic

    # def test_stream_delete(self, client: SpeckleClient, project: Project):
    #     deleted = client.project.delete(project.id)

    #     stream_get = client.project.get(project.id)

    #     assert deleted is True
    #     assert isinstance(stream_get, GraphQLException)
