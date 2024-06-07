"""This module contains an SDK for working with Speckle Automate."""

from speckle_automate.automation_context import AutomationContext
from speckle_automate.runner import execute_automate_function, run_function
from speckle_automate.schema import (
    AutomateBase,
    AutomationResult,
    AutomationRunData,
    AutomationStatus,
    ObjectResultLevel,
    ResultCase,
)

__all__ = [
    "AutomationContext",
    "AutomateBase",
    "AutomationStatus",
    "AutomationResult",
    "AutomationRunData",
    "ResultCase",
    "ObjectResultLevel",
    "run_function",
    "execute_automate_function",
]
