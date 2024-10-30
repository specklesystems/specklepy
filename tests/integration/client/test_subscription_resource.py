import asyncio
from typing import Optional

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
from specklepy.core.api.new_models import (
    Model,
    Project,
    ProjectModelsUpdatedMessage,
    ProjectUpdatedMessage,
    ProjectVersionsUpdatedMessage,
    UserProjectsUpdatedMessage,
    Version,
)
from tests.integration.conftest import create_version

WAIT_PERIOD = 5  # time in seconds


@pytest.mark.run()
class TestSubscriptionResource:
    @pytest.fixture
    def test_project(self, client: SpeckleClient) -> Project:
        project = client.project.create(
            ProjectCreateInput(name="Test project", description="", visibility=None)
        )
        return project

    @pytest.fixture
    def test_model(self, client: SpeckleClient, test_project: Project) -> Model:
        model1 = client.model.create(
            CreateModelInput(
                name="Test Model 1", description="", projectId=test_project.id
            )
        )
        return model1

    @pytest.mark.asyncio
    async def test_user_projects_updated(
        self,
        client: SpeckleClient,
    ) -> None:
        message: Optional[UserProjectsUpdatedMessage] = None

        task = None

        def callback(d: UserProjectsUpdatedMessage):
            nonlocal message
            message = d

        task = asyncio.create_task(client.subscribe.user_projects_updated(callback))

        await asyncio.sleep(WAIT_PERIOD)  # Give time to subscription to be setup

        input = ProjectCreateInput(name=None, description=None, visibility=None)
        created = client.project.create(input)

        await asyncio.sleep(WAIT_PERIOD)  # Give time for subscription to be triggered

        assert isinstance(message, UserProjectsUpdatedMessage)
        assert message.id == created.id
        assert message.type == UserProjectsUpdatedMessageType.ADDED
        assert isinstance(message.project, Project)
        task.cancel()

    @pytest.mark.asyncio
    async def test_project_models_updated(
        self, client: SpeckleClient, test_project: Project
    ) -> None:
        message: Optional[ProjectModelsUpdatedMessage] = None

        task = None

        def callback(d: ProjectModelsUpdatedMessage):
            nonlocal message
            message = d

        task = asyncio.create_task(
            client.subscribe.project_models_updated(callback, test_project.id)
        )

        await asyncio.sleep(WAIT_PERIOD)  # Give time to subscription to be setup

        input = CreateModelInput(
            name="my model", description="myDescription", projectId=test_project.id
        )
        created = client.model.create(input)

        await asyncio.sleep(WAIT_PERIOD)  # Give time for subscription to be triggered

        assert isinstance(message, ProjectModelsUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectModelsUpdatedMessageType.CREATED
        assert isinstance(message.model, Model)
        task.cancel()

    @pytest.mark.asyncio
    async def test_project_updated(
        self, client: SpeckleClient, test_project: Project
    ) -> None:
        message: Optional[ProjectUpdatedMessage] = None

        task = None

        def callback(d: ProjectUpdatedMessage):
            nonlocal message
            message = d

        task = asyncio.create_task(
            client.subscribe.project_updated(callback, test_project.id)
        )

        await asyncio.sleep(WAIT_PERIOD)  # Give time to subscription to be setup

        input = ProjectUpdateInput(id=test_project.id, name="This is my new name")
        created = client.project.update(input)

        await asyncio.sleep(WAIT_PERIOD)  # Give time for subscription to be triggered

        assert isinstance(message, ProjectUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectUpdatedMessageType.UPDATED
        assert isinstance(message.project, Project)
        task.cancel()

    @pytest.mark.asyncio
    async def test_project_versions_updated(
        self,
        client: SpeckleClient,
        test_project: Project,
        test_model: Model,
    ) -> None:
        message: Optional[ProjectVersionsUpdatedMessage] = None

        task = None

        def callback(d: ProjectVersionsUpdatedMessage):
            nonlocal message
            message = d

        task = asyncio.create_task(
            client.subscribe.project_versions_updated(callback, test_project.id)
        )

        await asyncio.sleep(WAIT_PERIOD)  # Give time to subscription to be setup

        created = create_version(client, test_project.id, test_model.id)

        await asyncio.sleep(WAIT_PERIOD)  # Give time for subscription to be triggered

        assert isinstance(message, ProjectVersionsUpdatedMessage)
        assert message.id == created.id
        assert message.type == ProjectVersionsUpdatedMessageType.UPDATED
        assert isinstance(message.version, Version)
        task.cancel()
