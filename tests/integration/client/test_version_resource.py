import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api import operations
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.version_inputs import (
    CreateVersionInput,
    DeleteVersionsInput,
    MarkReceivedVersionInput,
    MoveVersionsInput,
    UpdateVersionInput,
)
from specklepy.core.api.models import Model, Project, Version
from specklepy.core.api.new_models import ModelWithVersions
from specklepy.core.api.responses import ResourceCollection
from specklepy.logging.exceptions import GraphQLException
from specklepy.objects.base import Base
from specklepy.transports.server.server import ServerTransport


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
                name="Test Model 1", description="", projectId=test_project.id
            )
        )
        return model1

    @pytest.fixture
    def test_model_2(self, client: SpeckleClient, test_project: Project) -> Model:
        model2 = client.model.create(
            CreateModelInput(
                name="Test Model 2", description="", projectId=test_project.id
            )
        )
        return model2

    @pytest.fixture
    def test_version(
        self, client: SpeckleClient, test_project: Project, test_model_1: Model
    ) -> Version:
        remote = ServerTransport(test_project.id, client)
        objectId = operations.send(
            Base(applicationId="ASDF"), [remote], use_default_cache=False
        )
        input = CreateVersionInput(
            objectId=objectId, modelId=test_model_1.id, projectId=test_project.id
        )
        version_id = client.version.create(input)
        return client.version.get(version_id, test_project.id)

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
        assert result.totalCount == 1
        assert result.items[0].id == test_version.id

    def test_version_received(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        input_data = MarkReceivedVersionInput(
            versionId=test_version.id,
            projectId=test_project.id,
            sourceApplication="Integration test",
        )
        result = client.version.received(input_data)

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
        assert result.versions.totalCount == 1
        assert result.versions.items[0].id == test_version.id

    def test_version_update(self, client: SpeckleClient, test_version: Version):
        new_message = "MY new version message"
        input_data = UpdateVersionInput(versionId=test_version.id, message=new_message)
        updated_version = client.version.update(input_data)

        assert isinstance(updated_version, Version)
        assert updated_version.id == test_version.id
        assert updated_version.message == new_message
        assert updated_version.previewUrl == test_version.previewUrl

    def test_version_move_to_model(
        self,
        client: SpeckleClient,
        test_project: Project,
        test_version: Version,
        test_model_2: Model,
    ):
        input_data = MoveVersionsInput(
            targetModelName=test_model_2.name, versionIds=[test_version.id]
        )
        moved_model_id = client.version.move_to_model(input_data)

        assert isinstance(moved_model_id, str)
        assert moved_model_id == test_model_2.id
        moved_version = client.version.get(test_version.id, test_project.id)

        assert isinstance(moved_version, Version)
        assert moved_version.id == test_version.id
        assert moved_version.message == test_version.message
        assert moved_version.previewUrl == test_version.previewUrl

    def test_version_delete(
        self, client: SpeckleClient, test_version: Version, test_project: Project
    ):
        input_data = DeleteVersionsInput(versionIds=[test_version.id])

        response = client.version.delete(input_data)
        assert response is True

        with pytest.raises(GraphQLException):
            client.version.get(test_version.id, test_project.id)

        with pytest.raises(GraphQLException):
            client.version.delete(input_data)