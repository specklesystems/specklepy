import asyncio
from sys import platform
from typing import Dict

import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import (
    ModelIngestionStatus,
    ProjectModelIngestionUpdatedMessageType,
    ProjectModelsUpdatedMessageType,
    ProjectUpdatedMessageType,
    ProjectVersionsUpdatedMessageType,
    UserProjectsUpdatedMessageType,
)
from specklepy.core.api.inputs.model_ingestion_inputs import (
    ModelIngestionCreateInput,
    ModelIngestionReference,
    ModelIngestionRequestCancellationInput,
    ModelIngestionUpdateInput,
    ProjectModelIngestionSubscriptionInput,
    SourceDataInput,
)
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import (
    ProjectCreateInput,
    ProjectUpdateInput,
)
from specklepy.core.api.models import (
    Model,
    Project,
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
    Version,
)
from specklepy.core.api.models.current import ModelIngestion
from specklepy.core.api.models.subscription_messages import (
    ProjectModelIngestionUpdatedMessage,
)
from tests.integration.conftest import create_client, create_version, is_public

# WSL is slow AF, so for local runs, we're being extra generous
# For CI runs on linux,m a much smaller wait time is acceptable
SETUP_TIME_SECONDS = 1 if platform == "linux" else 4
MAX_WAIT_TIME_SECONDS = 0.75 if platform == "linux" else 5


@pytest.mark.run()
class TestSubscriptionResource:
    @pytest.fixture
    def subscription_client(
        self, host: str, user_dict: Dict[str, str]
    ) -> SpeckleClient:
        return create_client(host, user_dict["token"])

    @pytest.fixture
    def test_project(self, subscription_client: SpeckleClient) -> Project:
        project = subscription_client.project.create(
            ProjectCreateInput(name="Test project", description="", visibility=None)
        )
        return project

    @pytest.fixture
    def test_model(
        self, subscription_client: SpeckleClient, test_project: Project
    ) -> Model:
        model1 = subscription_client.model.create(
            CreateModelInput(
                name="Test Model 1", description="", project_id=test_project.id
            )
        )
        return model1

    @pytest.fixture
    def test_model_ingestion(
        self,
        subscription_client: SpeckleClient,
        test_project: Project,
        test_model: Model,
    ) -> ModelIngestion:
        project = subscription_client.model_ingestion.create(
            ModelIngestionCreateInput(
                project_id=test_project.id,
                model_id=test_model.id,
                progress_message="",
                source_data=SourceDataInput(
                    source_application_slug="pytest",
                    source_application_version="0.0.0",
                    file_name=None,
                    file_size_bytes=None,
                ),
            )
        )
        return project

    @pytest.mark.asyncio
    async def test_user_projects_updated(
        self,
        subscription_client: SpeckleClient,
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[UserProjectsUpdatedMessage] = loop.create_future()

        def callback(d: UserProjectsUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.user_projects_updated(callback)
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        input = ProjectCreateInput(name=None, description=None, visibility=None)
        created = subscription_client.project.create(input)

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, UserProjectsUpdatedMessage)
        assert message.id == created.id
        assert message.type == UserProjectsUpdatedMessageType.ADDED
        assert isinstance(message.project, Project)
        if not task.cancel():
            await task

    @pytest.mark.asyncio
    async def test_project_models_updated(
        self, subscription_client: SpeckleClient, test_project: Project
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectModelsUpdatedMessage] = loop.create_future()

        def callback(d: ProjectModelsUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_models_updated(
                callback, test_project.id
            )
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        input = CreateModelInput(
            name="my model", description="myDescription", project_id=test_project.id
        )
        created = subscription_client.model.create(input)

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, ProjectModelsUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectModelsUpdatedMessageType.CREATED
        assert isinstance(message.model, Model)

        if not task.cancel():
            await task

    @pytest.mark.asyncio
    async def test_project_updated(
        self, subscription_client: SpeckleClient, test_project: Project
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectUpdatedMessage] = loop.create_future()

        def callback(d: ProjectUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_updated(callback, test_project.id)
        )

        await asyncio.sleep(
            SETUP_TIME_SECONDS
        )  # Give time for subscription to be triggered

        input = ProjectUpdateInput(id=test_project.id, name="This is my new name")
        created = subscription_client.project.update(input)

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, ProjectUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectUpdatedMessageType.UPDATED
        assert isinstance(message.project, Project)
        if not task.cancel():
            await task

    @pytest.mark.asyncio
    async def test_project_versions_updated(
        self,
        subscription_client: SpeckleClient,
        test_project: Project,
        test_model: Model,
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectVersionsUpdatedMessage] = loop.create_future()

        def callback(d: ProjectVersionsUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_versions_updated(
                callback, test_project.id
            )
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        created = create_version(subscription_client, test_project.id, test_model.id)

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, ProjectVersionsUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectVersionsUpdatedMessageType.CREATED
        assert isinstance(message.version, Version)
        if not task.cancel():
            await task

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        is_public(), reason="The public API does not support these tests"
    )
    async def test_project_model_ingestion_cancellation(
        self,
        subscription_client: SpeckleClient,
        test_project: Project,
        test_model_ingestion: ModelIngestion,
    ) -> None:
        assert not test_model_ingestion.cancellation_requested

        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectModelIngestionUpdatedMessage] = (
            loop.create_future()
        )

        def callback(d: ProjectModelIngestionUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_model_ingestion_cancellation_requested(
                callback, test_project.id, ingestion_id=test_model_ingestion.id
            )
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        cancellation_request = ModelIngestionRequestCancellationInput(
            ingestion_id=test_model_ingestion.id,
            project_id=test_project.id,
            cancellation_message="Please cancel",
        )
        created = subscription_client.model_ingestion.request_cancellation(
            cancellation_request
        )
        assert created.id == test_model_ingestion.id
        assert created.cancellation_requested
        assert created.status_data.status == ModelIngestionStatus.PROCESSING

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, ProjectModelIngestionUpdatedMessage)
        assert message.model_ingestion.id == created.id
        assert message.model_ingestion.cancellation_requested
        assert (
            message.type
            == ProjectModelIngestionUpdatedMessageType.CANCELLATION_REQUESTED
        )
        assert created.status_data.status == ModelIngestionStatus.PROCESSING
        if not task.cancel():
            await task

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        is_public(), reason="The public API does not support these tests"
    )
    async def test_project_model_ingestion_cancellation_isnt_triggered_by_updates(
        self,
        subscription_client: SpeckleClient,
        test_project: Project,
        test_model_ingestion: ModelIngestion,
    ) -> None:
        assert not test_model_ingestion.cancellation_requested

        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectModelIngestionUpdatedMessage] = (
            loop.create_future()
        )

        def callback(d: ProjectModelIngestionUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_model_ingestion_cancellation_requested(
                callback, test_project.id, ingestion_id=test_model_ingestion.id
            )
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        cancellation_request = ModelIngestionUpdateInput(
            ingestion_id=test_model_ingestion.id,
            project_id=test_project.id,
            progress=None,
            progress_message="this is just an ordinary update",
        )
        created = subscription_client.model_ingestion.update_progress(
            cancellation_request
        )
        assert created.id == test_model_ingestion.id
        assert not created.cancellation_requested
        assert created.status_data.status == ModelIngestionStatus.PROCESSING

        await asyncio.sleep(MAX_WAIT_TIME_SECONDS)

        assert (
            not future.done()
        )  # make sure the sub did not call back and resolve the future

        if not task.cancel():
            await task

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        is_public(), reason="The public API does not support these tests"
    )
    async def test_project_model_ingestion_updates(
        self,
        subscription_client: SpeckleClient,
        test_project: Project,
        test_model_ingestion: ModelIngestion,
    ) -> None:
        assert not test_model_ingestion.cancellation_requested

        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectModelIngestionUpdatedMessage] = (
            loop.create_future()
        )

        def callback(d: ProjectModelIngestionUpdatedMessage):
            nonlocal future
            future.set_result(d)

        task = asyncio.create_task(
            subscription_client.subscription.project_model_ingestion_updated(
                callback,
                input=ProjectModelIngestionSubscriptionInput(
                    project_id=test_project.id,
                    ingestion_reference=ModelIngestionReference(
                        ingestion_id=test_model_ingestion.id, model_id=None
                    ),
                ),
                # ingestion_id=test_model_ingestion.id,
            )
        )

        await asyncio.sleep(SETUP_TIME_SECONDS)  # Give time to subscription to be setup

        progress_message = "this is just an ordinary update"
        cancellation_request = ModelIngestionUpdateInput(
            ingestion_id=test_model_ingestion.id,
            project_id=test_project.id,
            progress=None,
            progress_message=progress_message,
        )
        created = subscription_client.model_ingestion.update_progress(
            cancellation_request
        )
        assert created.id == test_model_ingestion.id
        assert not created.cancellation_requested
        assert created.status_data.status == ModelIngestionStatus.PROCESSING

        message = await asyncio.wait_for(future, timeout=MAX_WAIT_TIME_SECONDS)

        assert isinstance(message, ProjectModelIngestionUpdatedMessage)
        assert message.model_ingestion.id == created.id
        assert not message.model_ingestion.cancellation_requested
        assert message.type == ProjectModelIngestionUpdatedMessageType.UPDATED
        assert message.model_ingestion.status_data.progress_message == progress_message
        assert created.status_data.status == ModelIngestionStatus.PROCESSING
        if not task.cancel():
            await task
