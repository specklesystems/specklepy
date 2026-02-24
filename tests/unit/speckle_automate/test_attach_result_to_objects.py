"""Unit tests for AutomationContext.attach_result_to_objects contract."""

from unittest.mock import MagicMock

import pytest

from speckle_automate import AutomationContext
from speckle_automate.schema import (
    AutomationRunData,
    ObjectResultLevel,
    VersionCreationTrigger,
    VersionCreationTriggerPayload,
)
from specklepy.objects.base import Base


def _minimal_automation_context() -> AutomationContext:
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
    return AutomationContext(
        automation_run_data=run_data,
        speckle_client=MagicMock(),
        _server_transport=MagicMock(),
        _speckle_token="",
    )


def test_attach_result_to_objects_accepts_empty_list() -> None:
    """Empty affected_objects appends one result case with no object IDs."""
    ctx = _minimal_automation_context()
    assert len(ctx._automation_result.object_results) == 0

    ctx.attach_result_to_objects(
        ObjectResultLevel.WARNING,
        "SkippedRule",
        [],
        message="No elements to check.",
    )

    assert len(ctx._automation_result.object_results) == 1
    case = ctx._automation_result.object_results[0]
    assert case.level == ObjectResultLevel.WARNING
    assert case.category == "SkippedRule"
    assert case.object_app_ids == {}
    assert case.message == "No elements to check."


def test_attach_result_to_objects_with_objects_appends_case_with_ids() -> None:
    """Single or multiple objects with id produce result case with object_app_ids."""
    ctx = _minimal_automation_context()
    obj1 = Base()
    obj1.id = "id-one"
    obj1.applicationId = "app-one"
    obj2 = Base()
    obj2.id = "id-two"

    ctx.attach_result_to_objects(
        ObjectResultLevel.ERROR,
        "BadType",
        [obj1, obj2],
        message="Invalid type.",
    )

    assert len(ctx._automation_result.object_results) == 1
    case = ctx._automation_result.object_results[0]
    assert case.level == ObjectResultLevel.ERROR
    assert case.category == "BadType"
    assert case.object_app_ids == {"id-one": "app-one", "id-two": None}
    assert case.message == "Invalid type."


def test_attach_result_to_objects_raises_when_object_has_no_id() -> None:
    """At least one object without id raises."""
    ctx = _minimal_automation_context()
    obj = Base()
    obj.id = None

    with pytest.raises(Exception, match="results to objects with an id"):
        ctx.attach_result_to_objects(
            ObjectResultLevel.ERROR,
            "Bad",
            obj,
            message="No id.",
        )

    assert len(ctx._automation_result.object_results) == 0


def test_attach_info_to_objects_accepts_empty_list() -> None:
    """attach_info_to_objects (convenience method) also accepts empty list."""
    ctx = _minimal_automation_context()

    ctx.attach_info_to_objects("VersionLevel", [], message="No levels in model.")

    assert len(ctx._automation_result.object_results) == 1
    case = ctx._automation_result.object_results[0]
    assert case.level == ObjectResultLevel.INFO
    assert case.category == "VersionLevel"
    assert case.object_app_ids == {}
