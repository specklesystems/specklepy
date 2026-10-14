from unittest.mock import MagicMock

import pytest

from speckle_automate import AutomationContext
from speckle_automate.schema import (
    AutomationRunData,
    VersionCreationTrigger,
    VersionCreationTriggerPayload,
)
from specklepy.api import operations
from specklepy.bundle.send import SendOptions, SendResult
from specklepy.objects.base import Base


@pytest.fixture
def ctx() -> AutomationContext:
    run_data = AutomationRunData(
        project_id="p",
        speckle_server_url="http://localhost",
        automation_id="a",
        automation_run_id="r",
        function_run_id="f",
        triggers=[
            VersionCreationTrigger(
                trigger_type="versionCreation",
                payload=VersionCreationTriggerPayload(model_id="m", version_id="v"),
            )
        ],
    )
    return AutomationContext(automation_run_data=run_data, speckle_client=MagicMock())


def test_receive_version_bundle(ctx: AutomationContext, monkeypatch) -> None:
    received = MagicMock()
    receive3 = MagicMock(return_value=received)
    monkeypatch.setattr(operations, "receive3", receive3)

    assert ctx.receive_version_bundle(include_geometry=False) is received
    receive3.assert_called_once_with(
        ctx.speckle_client.account, "p", "m", "v", include_geometry=False
    )


def test_create_new_version_in_project_bundle(
    ctx: AutomationContext, monkeypatch
) -> None:
    result = SendResult("p", "target", "new_version", "ingestion", 1)
    send3 = MagicMock(return_value=result)
    monkeypatch.setattr(operations, "send3", send3)
    builder = MagicMock()
    options = SendOptions(message="hello")

    assert ctx.create_new_version_in_project_bundle(builder, "target", options) is (
        result
    )
    send3.assert_called_once_with(
        ctx.speckle_client.account, "p", "target", builder, options
    )
    assert ctx._automation_result.result_versions == ["new_version"]


def test_create_new_version_in_project_bundle_rejects_trigger_model(
    ctx: AutomationContext, monkeypatch
) -> None:
    send3 = MagicMock()
    monkeypatch.setattr(operations, "send3", send3)

    with pytest.raises(ValueError):
        ctx.create_new_version_in_project_bundle(MagicMock(), "m")
    send3.assert_not_called()


def test_legacy_members_are_deprecated(ctx: AutomationContext) -> None:
    with pytest.deprecated_call():
        assert ctx._speckle_token is ctx.speckle_client.account.token
    with pytest.deprecated_call(), pytest.raises(ValueError):
        ctx.create_new_version_in_project(Base(), "m")
