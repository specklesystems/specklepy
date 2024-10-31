import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.inputs.model_inputs import (
    CreateModelInput,
    DeleteModelInput,
    UpdateModelInput,
)
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.models.current import ProjectWithModels, ResourceCollection
from specklepy.core.api.models.deprecated import Model, Project
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestModelResource:
    @pytest.fixture()
    def test_project(self, client: SpeckleClient) -> Project:
        project = client.project.create(
            ProjectCreateInput(name="Test project", description="", visibility=None)
        )
        return project

    @pytest.fixture()
    def test_model(self, client: SpeckleClient, test_project: Project) -> Model:
        model = client.model.create(
            CreateModelInput(
                name="Test Model", description="", projectId=test_project.id
            )
        )
        return model

    @pytest.mark.parametrize(
        "name, description",
        [
            ("My Model", "My model description"),
            ("my/nested/model", None),
        ],
    )
    def test_model_create(
        self, client: SpeckleClient, test_project: Project, name: str, description: str
    ):
        input = CreateModelInput(
            name=name, description=description, projectId=test_project.id
        )
        result = client.model.create(input)

        assert isinstance(result, Model)
        assert result.name.lower() == name.lower()
        assert result.description == description

    def test_model_get(
        self, client: SpeckleClient, test_model: Model, test_project: Project
    ):
        result = client.model.get(test_model.id, test_project.id)

        assert isinstance(result, Model)
        assert result.id == test_model.id
        assert result.name == test_model.name
        assert result.description == test_model.description
        assert result.createdAt == test_model.createdAt
        assert result.updatedAt == test_model.updatedAt

    def test_get_models(
        self, client: SpeckleClient, test_project: Project, test_model: Model
    ):
        result = client.model.get_models(test_project.id)

        assert isinstance(result, ResourceCollection)
        assert len(result.items) == 1
        assert result.totalCount == 1
        assert result.items[0].id == test_model.id

    def test_project_get_models(
        self, client: SpeckleClient, test_project: Project, test_model: Model
    ):
        result = client.project.get_with_models(test_project.id)

        assert isinstance(result, ProjectWithModels)
        assert result.id == test_project.id
        assert len(result.models.items) == 1
        assert result.models.totalCount == 1
        assert result.models.items[0].id == test_model.id

    def test_model_update(
        self, client: SpeckleClient, test_model: Model, test_project: Project
    ):
        new_name = "MY new name"
        new_description = "MY new desc"

        update_data = UpdateModelInput(
            id=test_model.id,
            name=new_name,
            description=new_description,
            projectId=test_project.id,
        )

        updated_model = client.model.update(update_data)

        assert isinstance(updated_model, Model)
        assert updated_model.id == test_model.id
        assert updated_model.name.lower() == new_name.lower()
        assert updated_model.description == new_description
        assert updated_model.updatedAt >= test_model.updatedAt

    def test_model_delete(
        self, client: SpeckleClient, test_model: Model, test_project: Project
    ):
        delete_data = DeleteModelInput(id=test_model.id, projectId=test_project.id)

        response = client.model.delete(delete_data)
        assert response is True

        with pytest.raises(GraphQLException):
            client.model.get(test_model.id, test_project.id)

        with pytest.raises(GraphQLException):
            client.model.delete(delete_data)
