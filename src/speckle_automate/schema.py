""""""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from stringcase import camelcase


class AutomateBase(BaseModel):
    """Use this class as a base model for automate related DTO."""

    model_config = ConfigDict(alias_generator=camelcase, populate_by_name=True)


class AutomationRunData(BaseModel):
    """Values of the project / model that triggered the run of this function."""

    project_id: str
    model_id: str
    branch_name: str
    version_id: str
    speckle_server_url: str

    automation_id: str
    automation_revision_id: str
    automation_run_id: str

    function_id: str
    function_name: str
    function_logo: Optional[str]

    model_config = ConfigDict(
        alias_generator=camelcase, populate_by_name=True, protected_namespaces=()
    )


class AutomationStatus(str, Enum):
    """Set the status of the automation."""

    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"


class ObjectResultLevel(str, Enum):
    """Possible status message levels for object reports."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ResultCase(AutomateBase):
    """A result case."""

    category: str
    level: ObjectResultLevel
    object_ids: List[str]
    message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    visual_overrides: Optional[Dict[str, Any]]


class AutomationResult(AutomateBase):
    """Schema accepted by the Speckle server as a result for an automation run."""

    elapsed: float = 0
    result_view: Optional[str] = None
    result_versions: List[str] = Field(default_factory=list)
    blobs: List[str] = Field(default_factory=list)
    run_status: AutomationStatus = AutomationStatus.RUNNING
    status_message: Optional[str] = None
    object_results: list[ResultCase] = Field(default_factory=list)
