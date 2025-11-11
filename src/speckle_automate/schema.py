""""""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AutomateBase(BaseModel):
    """Use this class as a base model for automate related DTO."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class VersionCreationTriggerPayload(AutomateBase):
    """Represents the version creation trigger payload."""

    model_id: str
    version_id: str


class VersionCreationTrigger(AutomateBase):
    """Represents a single version creation trigger for the automation run."""

    trigger_type: Literal["versionCreation"]
    payload: VersionCreationTriggerPayload


class AutomationRunData(BaseModel):
    """Values of the project / model that triggered the run of this function."""

    project_id: str
    speckle_server_url: str
    automation_id: str
    automation_run_id: str
    function_run_id: str

    triggers: list[VersionCreationTrigger]

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, protected_namespaces=()
    )


class TestAutomationRunData(BaseModel):
    """Values of the run created in the test automation for local test results."""

    automation_run_id: str
    function_run_id: str

    triggers: list[VersionCreationTrigger]

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, protected_namespaces=()
    )


class AutomationStatus(str, Enum):
    """Set the status of the automation."""

    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    EXCEPTION = "EXCEPTION"


class ObjectResultLevel(str, Enum):
    """Possible status message levels for object reports."""

    SUCCESS = "SUCCESS"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ResultCase(AutomateBase):
    """A result case."""

    category: str
    level: ObjectResultLevel
    object_app_ids: dict[str, str | None]
    message: str | None
    metadata: dict[str, Any] | None
    visual_overrides: dict[str, Any] | None


class AutomationResult(AutomateBase):
    """Schema accepted by the Speckle server as a result for an automation run."""

    elapsed: float = 0
    result_view: str | None = None
    result_versions: list[str] = Field(default_factory=list)
    blobs: list[str] = Field(default_factory=list)
    run_status: AutomationStatus = AutomationStatus.RUNNING
    status_message: str | None = None
    object_results: list[ResultCase] = Field(default_factory=list)
    version_result: dict[str, Any] | None = None
