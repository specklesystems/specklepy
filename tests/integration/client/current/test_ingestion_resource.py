import pytest

from specklepy.core.api.client import SpeckleClient  # todo: change to non-core
from specklepy.core.api.inputs.ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionSuccessInput,
    SourceDataInput,
)
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.models.current import (
    Model,
    ModelIngestion,
    Project,
    ProjectVisibility,
    Version,
)
from specklepy.logging.exceptions import GraphQLException


@pytest.mark.run()
class TestIngestionResource:
    @pytest.fixture
    def project(self, client: SpeckleClient):
        return client.project.create(
            ProjectCreateInput(
                name="test", description=None, visibility=ProjectVisibility.PUBLIC
            )
        )

    @pytest.fixture
    def model(self, client: SpeckleClient, project: Project):
        return client.model.create(
            CreateModelInput(name="test", description=None, project_id=project.id)
        )

    @pytest.fixture()
    def ingestion(
        self, client: SpeckleClient, model: Model, project: Project
    ) -> ModelIngestion:
        input = ModelIngestionCreateInput(
            model_id=model.id,
            project_id=project.id,
            progress_message="Starting processing",
            source_data=SourceDataInput(
                source_application_slug="pytest",
                source_application_version="0.0.0",
                file_name=None,
                file_size_bytes=None,
            ),
        )

        return client.ingestion.create(input)

    def test_create_and_error(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionFailedInput(
            ingestion_id=ingestion.id,
            project_id=project.id,  # TODO: Check with Gergo
            error_reason="Failed to integration test an error",
            error_stack_trace="over here in test_error",
        )
        res = client.ingestion.fail_with_error(input)
        assert isinstance(res, ModelIngestion)

    def test_create_and_complete(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionSuccessInput(
            ingestion_id=ingestion.id,
            root_object_id="asdfasdfasdfasfd",
            project_id=project.id,
        )
        res = client.ingestion.complete(input)
        assert isinstance(res, str)
        version = client.version.get(res, project.id)
        assert isinstance(version, Version)

    def test_create_and_cancel(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionCancelledInput(
            ingestion_id=ingestion.id,
            project_id=project.id,
            cancellation_message="This was cancelled for testing purposes",
        )
        res = client.ingestion.fail_with_cancelled(input)
        assert isinstance(res, str)
        version = client.version.get(res, project.id)
        assert isinstance(version, Version)

    def test_error_non_existent_ingestion(
        self, client: SpeckleClient, project: Project
    ):
        with pytest.raises(GraphQLException):
            input = ModelIngestionFailedInput(
                ingestion_id="Non-existent-ingestion",
                project_id=project.id,
                error_reason="Failed to integration test an error",
                error_stack_trace="over here in test_error",
            )
            res = client.ingestion.fail_with_error(input)
            assert isinstance(res, ModelIngestion)

    def test_complete_failed_non_existent_ingestion(
        self, client: SpeckleClient, project: Project
    ):
        with pytest.raises(GraphQLException):
            input = ModelIngestionFailedInput(
                ingestion_id="Non-existent-ingestion",
                project_id=project.id,
                error_reason="Failed to integration test an error",
                error_stack_trace="over here in test_error",
            )
            res = client.ingestion.fail_with_error(input)
            assert isinstance(res, ModelIngestion)
