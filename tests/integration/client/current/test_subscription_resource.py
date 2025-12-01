import asyncio
from sys import platform
from typing import Dict

import pytest

from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import (
    ProjectModelsUpdatedMessageType,
    ProjectUpdatedMessageType,
    ProjectVersionsUpdatedMessageType,
    UserProjectsUpdatedMessageType,
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
from tests.integration.conftest import create_client, create_version

# WSL is slow AF, so for local runs, we're being extra generous
# For CI runs on linux,m a much smaller wait time is acceptable
SETUP_TIME_SECONDS = 0.5 if platform == "linux" else 4
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

    @pytest.mark.asyncio
    async def test_user_projects_updated(
        self,
        subscription_client: SpeckleClient,
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[UserProjectsUpdatedMessage] = loop.create_future()

        task = None

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
        task.cancel()
        await task

    @pytest.mark.asyncio
    async def test_project_models_updated(
        self, subscription_client: SpeckleClient, test_project: Project
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectModelsUpdatedMessage] = loop.create_future()
        task = None

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
        task.cancel()
        await task

    @pytest.mark.asyncio
    async def test_project_updated(
        self, subscription_client: SpeckleClient, test_project: Project
    ) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProjectUpdatedMessage] = loop.create_future()
        task = None

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
        task.cancel()
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

        task = None

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
        task.cancel()
        await task
