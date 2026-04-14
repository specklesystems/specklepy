import time

import pytest

from specklepy.core.api.client import SpeckleClient
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionCreateInput,
    SourceDataInput,
)
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.models.current import Model, ModelIngestion, Project
from specklepy.progress.ingestion_progress import IngestionProgressManager
from tests.integration.conftest import is_public


@pytest.mark.run()
@pytest.mark.skipif(
    is_public(), reason="The public API does not support model ingestion api"
)
class TestIngestionProgressManager:
    @pytest.fixture
    def project(self, client: SpeckleClient) -> Project:
        return client.project.create(
            ProjectCreateInput(
                name="test", description=None, visibility=ProjectVisibility.PUBLIC
            )
        )

    @pytest.fixture
    def model(self, client: SpeckleClient, project: Project) -> Model:
        return client.model.create(
            CreateModelInput(name="test", description=None, project_id=project.id)
        )

    @pytest.fixture
    def model_ingestion(
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

        return client.model_ingestion.create(input)

    def test_progress_respects_throttle(
        self,
        client: SpeckleClient,
        model_ingestion: ModelIngestion,
    ) -> None:
        EXPECTED_MESSAGE = "This is a test ingestion message"
        EXPECTED_PROGRESS = 0.123123
        UPDATE_INTERVAL_SECONDS = 1

        sut = IngestionProgressManager(
            speckle_client=client,
            ingestion=model_ingestion,
            update_interval_seconds=UPDATE_INTERVAL_SECONDS,
        )

        assert sut.should_report_progress() is True

        res = sut.report(EXPECTED_MESSAGE, EXPECTED_PROGRESS)

        assert sut.should_report_progress() is False

        time.sleep(UPDATE_INTERVAL_SECONDS + 0.5)

        assert sut.should_report_progress() is True
        assert sut.should_report_progress() is True

        assert res.status_data.progress_message == EXPECTED_MESSAGE

    def test_progress_no_throttle(
        self,
        client: SpeckleClient,
        model_ingestion: ModelIngestion,
    ) -> None:
        EXPECTED_MESSAGE = "This is a test ingestion message"
        EXPECTED_PROGRESS = 0.123123
        UPDATE_INTERVAL_SECONDS = 0

        sut = IngestionProgressManager(
            speckle_client=client,
            ingestion=model_ingestion,
            update_interval_seconds=UPDATE_INTERVAL_SECONDS,
        )

        assert sut.should_report_progress() is True

        res = sut.report(EXPECTED_MESSAGE, EXPECTED_PROGRESS)

        assert sut.should_report_progress() is True
        assert sut.should_report_progress() is True

        assert res.status_data.progress_message == EXPECTED_MESSAGE
