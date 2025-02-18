import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.inputs.model_inputs import CreateModelInput, ModelVersionsFilter
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.version_inputs import (
    DeleteVersionsInput,
    MarkReceivedVersionInput,
    MoveVersionsInput,
    UpdateVersionInput,
)
from specklepy.core.api.models import (
    Model,
    ModelWithVersions,
    Project,
    ResourceCollection,
    Version,
)
from specklepy.logging.exceptions import GraphQLException
from tests.integration.conftest import create_version


@pytest.mark.run()
class TestVersionResource:
    @pytest.fixture
    def test_project(self, client: SpeckleClient) -> Project:
        project = client.project.create(
            ProjectCreateInput(name="Test project", description="", visibility=None)
        )
        return project

    @pytest.fixture
    def test_model_1(self, client: SpeckleClient, test_project: Project) -> Model:
        model1 = client.model.create(
            CreateModelInput(
                name="Test Model 1", description="", project_id=test_project.id
            )
        )
        return model1

    @pytest.fixture
    def test_model_2(self, client: SpeckleClient, test_project: Project) -> Model:
        model2 = client.model.create(
            CreateModelInput(
                name="Test Model 2", description="", project_id=test_project.id
            )
        )
        return model2

    @pytest.fixture
    def test_version(
        self, client: SpeckleClient, test_project: Project, test_model_1: Model
    ) -> Version:
        return create_version(client, test_project.id, test_model_1.id)

    def test_version_get(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        result = client.version.get(test_version.id, test_project.id)

        assert isinstance(result, Version)
        assert result.id == test_version.id
        assert result.message == test_version.message

    def test_versions_get(
        self,
        client: SpeckleClient,
        test_model_1: Model,
        test_project: Project,
        test_version: Version,
    ):
        result = client.version.get_versions(test_model_1.id, test_project.id)

        assert isinstance(result, ResourceCollection)
        assert len(result.items) == 1
        assert result.total_count == 1
        assert result.items[0].id == test_version.id

    def test_versions_get_with_filter(
        self,
        client: SpeckleClient,
        test_model_1: Model,
        test_project: Project,
        test_version: Version,
    ):
        filter = ModelVersionsFilter(
            priority_ids=[test_version.id], priority_ids_only=True
        )

        result = client.version.get_versions(
            test_model_1.id, test_project.id, filter=filter
        )

        assert isinstance(result, ResourceCollection)
        assert len(result.items) == 1
        assert result.total_count == 1
        assert result.items[0].id == test_version.id

    def test_version_received(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        input = MarkReceivedVersionInput(
            version_id=test_version.id,
            project_id=test_project.id,
            source_application="Integration test",
        )
        result = client.version.received(input)

        assert result is True

    def test_model_get_with_versions(
        self,
        client: SpeckleClient,
        test_model_1: Model,
        test_project: Project,
        test_version: Version,
    ):
        result = client.model.get_with_versions(test_model_1.id, test_project.id)

        assert isinstance(result, ModelWithVersions)
        assert result.id == test_model_1.id
        assert len(result.versions.items) == 1
        assert result.versions.total_count == 1
        assert result.versions.items[0].id == test_version.id

    def test_model_get_with_versions_with_filter(
        self,
        client: SpeckleClient,
        test_model_1: Model,
        test_project: Project,
        test_version: Version,
    ):
        filter = ModelVersionsFilter(
            priority_ids=[test_version.id], priority_ids_only=True
        )

        result = client.model.get_with_versions(
            test_model_1.id, test_project.id, versions_filter=filter
        )

        assert isinstance(result, ModelWithVersions)
        assert len(result.versions.items) == 1
        assert result.versions.total_count == 1
        assert isinstance(result.versions, ResourceCollection)
        assert result.versions.items[0].id == test_version.id

    def test_version_update(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        new_message = "MY new version message"
        input = UpdateVersionInput(
            version_id=test_version.id, project_id=test_project.id, message=new_message
        )
        updated_version = client.version.update(input)

        assert isinstance(updated_version, Version)
        assert updated_version.id == test_version.id
        assert updated_version.message == new_message
        assert updated_version.preview_url == test_version.preview_url

    def test_version_move_to_model(
        self,
        client: SpeckleClient,
        test_project: Project,
        test_version: Version,
        test_model_2: Model,
    ):
        input = MoveVersionsInput(
            target_model_name=test_model_2.name,
            version_ids=[test_version.id],
            project_id=test_project.id,
        )
        moved_model_id = client.version.move_to_model(input)

        assert isinstance(moved_model_id, str)
        assert moved_model_id == test_model_2.id
        moved_version = client.version.get(test_version.id, test_project.id)

        assert isinstance(moved_version, Version)
        assert moved_version.id == test_version.id
        assert moved_version.message == test_version.message
        assert moved_version.preview_url == test_version.preview_url

    def test_version_delete(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        input = DeleteVersionsInput(
            version_ids=[test_version.id], project_id=test_project.id
        )

        response = client.version.delete(input)
        assert response is True

        with pytest.raises(GraphQLException):
            client.version.get(test_version.id, test_project.id)

        with pytest.raises(GraphQLException):
            client.version.delete(input)
