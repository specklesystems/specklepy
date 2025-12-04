from datetime import datetime

import pytest

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import ModelIngestionStatus
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionCancelledInput,
    ModelIngestionCreateInput,
    ModelIngestionFailedInput,
    ModelIngestionSuccessInput,
    ModelIngestionUpdateInput,
    SourceDataInput,
)
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.models.current import (
    Model,
    ModelIngestion,
    ModelIngestionStatusData,
    Project,
    ProjectVisibility,
    Version,
)
from specklepy.logging.exceptions import GraphQLException
from specklepy.objects.base import Base
from specklepy.transports.server.server import ServerTransport
from tests.integration.conftest import is_public


@pytest.mark.run()
@pytest.mark.skipif(is_public(), reason="The public API does not support these tests")
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

        ingestion = client.model_ingestion.create(input)
        assert isinstance(ingestion, ModelIngestion)
        assert isinstance(ingestion.id, str)
        assert isinstance(ingestion.created_at, datetime)
        assert isinstance(ingestion.updated_at, datetime)
        assert isinstance(ingestion.cancellation_requested, bool)
        assert isinstance(ingestion.model_id, str)
        assert isinstance(ingestion.status_data, ModelIngestionStatusData)
        assert isinstance(ingestion.status_data.progress_message, str | None)
        assert ingestion.status_data.status == ModelIngestionStatus.PROCESSING
        assert not ingestion.cancellation_requested
        assert ingestion.model_id == model.id

        return ingestion

    def test_update_progress(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        def update(progress: float | None, message: str):
            input = ModelIngestionUpdateInput(
                ingestion_id=ingestion.id,
                project_id=project.id,
                progress=progress,
                progress_message=message,
            )
            res = client.model_ingestion.update_progress(input)

            assert isinstance(res, ModelIngestion)
            assert res.status_data.progress_message == message
            assert not res.cancellation_requested
            assert res.status_data.status == ModelIngestionStatus.PROCESSING

        update(None, "None")
        update(0.1, "0.1")
        update(0.5, "Whoa-oh! We're half way there!")
        update(1, "Finished")
        update(0.2, "Back to processing again")

    def test_error(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionFailedInput(
            ingestion_id=ingestion.id,
            project_id=project.id,
            error_reason="Failed to integration test an error",
            error_stacktrace="over here in test_error",
        )

        res = client.model_ingestion.fail_with_error(input)

        assert isinstance(res, ModelIngestion)
        assert res.status_data.progress_message is None
        assert not res.cancellation_requested
        assert res.status_data.status == ModelIngestionStatus.FAILED

        # trying to fail for a second time should throw
        # with pytest.raises(GraphQLException):
        #     _ = client.ingestion.fail_with_error(input)

    def test_complete(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        remote = ServerTransport(project.id, client)
        object_id = operations.send(
            Base(applicationId="ASDFGHJKL"), [remote], use_default_cache=False
        )
        input = ModelIngestionSuccessInput(
            ingestion_id=ingestion.id,
            root_object_id=object_id,
            project_id=project.id,
        )

        res = client.model_ingestion.complete(input)

        assert isinstance(res, str)
        version = client.version.get(res, project.id)
        assert isinstance(version, Version)

        # trying to complete for a second time should throw
        # with pytest.raises(GraphQLException):
        #     _ = client.ingestion.complete(input)

    def test_cancel(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionCancelledInput(
            ingestion_id=ingestion.id,
            project_id=project.id,
            cancellation_message="This was cancelled for testing purposes",
        )
        res = client.model_ingestion.fail_with_cancel(input)
        assert isinstance(res, ModelIngestion)
        assert res.status_data.progress_message is None
        assert not res.cancellation_requested
        assert res.status_data.status == ModelIngestionStatus.CANCELLED

        # Cancel again, should be idempotent
        res = client.model_ingestion.fail_with_cancel(input)
        assert res.status_data.progress_message is None
        assert not res.cancellation_requested
        assert res.status_data.status == ModelIngestionStatus.CANCELLED

    def test_error_non_existent_ingestion(
        self, client: SpeckleClient, project: Project
    ):
        input = ModelIngestionFailedInput(
            ingestion_id="Non-existent-ingestion",
            project_id=project.id,
            error_reason="Failed to integration test an error",
            error_stacktrace="over here in test_error",
        )
        with pytest.raises(GraphQLException):
            _ = client.model_ingestion.fail_with_error(input)

    def test_complete_failed_non_existent_ingestion(
        self, client: SpeckleClient, project: Project
    ):
        input = ModelIngestionFailedInput(
            ingestion_id="Non-existent-ingestion",
            project_id=project.id,
            error_reason="Failed to integration test an error",
            error_stacktrace="over here in test_error",
        )
        with pytest.raises(GraphQLException):
            _ = client.model_ingestion.fail_with_error(input)

    def test_complete_non_existent_root_object(
        self, client: SpeckleClient, ingestion: ModelIngestion, project: Project
    ):
        input = ModelIngestionSuccessInput(
            ingestion_id=ingestion.id,
            root_object_id="asdfasdfasdfasfd",
            project_id=project.id,
        )
        with pytest.raises(GraphQLException):
            _ = client.model_ingestion.complete(input)
