"""Function execution module.

Provides mechanisms to execute any function,
 that conforms to the AutomateFunction "interface"
"""
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Callable, Optional, TypeVar, Union, overload

from speckle_automate.automation_context import AutomationContext
from speckle_automate.schema import AutomateBase, AutomationStatus

T = TypeVar("T", bound=AutomateBase)

AutomateFunction = Callable[[AutomationContext, T], None]
AutomateFunctionWithoutInputs = Callable[[AutomationContext], None]


@overload
def execute_automate_function(
    automate_function: AutomateFunction[T],
    input_schema: type[T],
) -> None:
    ...


@overload
def execute_automate_function(automate_function: AutomateFunctionWithoutInputs) -> None:
    ...


def execute_automate_function(
    automate_function: Union[AutomateFunction[T], AutomateFunctionWithoutInputs],
    input_schema: Optional[type[T]] = None,
):
    """Runs the provided automate function with the input schema."""
    # first arg is the python file name, we do not need that
    args = sys.argv[1:]

    if len(args) < 2:
        raise ValueError("too few arguments specified need minimum 2")

    if len(args) > 4:
        raise ValueError("too many arguments specified, max supported is 4")

    # we rely on a command name convention to decide what to do.
    # this is here, so that the function authors do not see any of this
    command = args[0]

    if command == "generate_schema":
        path = Path(args[1])
        schema = json.dumps(
            input_schema.model_json_schema(by_alias=True) if input_schema else {}
        )
        path.write_text(schema)

    elif command == "run":
        automation_run_data = args[1]
        function_inputs = args[2]

        speckle_token = os.environ.get("SPECKLE_TOKEN", None)
        if not speckle_token and len(args) != 4:
            raise ValueError("Cannot get speckle token from arguments or environment")

        speckle_token = speckle_token if speckle_token else args[3]
        automation_context = AutomationContext.initialize(
            automation_run_data, speckle_token
        )

        inputs = (
            input_schema.model_validate_json(function_inputs)
            if input_schema
            else input_schema
        )

        if inputs:
            automation_context = run_function(
                automation_context,
                automate_function,  # type: ignore
                inputs,
            )
        else:
            automation_context = run_function(
                automation_context,
                automate_function,  # type: ignore
            )

        exit_code = (
            0 if automation_context.run_status == AutomationStatus.SUCCEEDED else 1
        )
        exit(exit_code)

    else:
        raise NotImplementedError(f"Command: '{command}' is not supported.")


@overload
def run_function(
    automation_context: AutomationContext,
    automate_function: AutomateFunction[T],
    inputs: T,
) -> AutomationContext:
    ...


@overload
def run_function(
    automation_context: AutomationContext,
    automate_function: AutomateFunctionWithoutInputs,
) -> AutomationContext:
    ...


def run_function(
    automation_context: AutomationContext,
    automate_function: Union[AutomateFunction[T], AutomateFunctionWithoutInputs],
    inputs: Optional[T] = None,
) -> AutomationContext:
    """Run the provided function with the automate sdk context."""
    automation_context.report_run_status()

    try:
        # avoiding complex type gymnastics here on the internals.
        # the external type overloads make this correct
        if inputs:
            automate_function(automation_context, inputs)  # type: ignore
        else:
            automate_function(automation_context)  # type: ignore

        # the function author forgot to mark the function success
        if automation_context.run_status not in [
            AutomationStatus.FAILED,
            AutomationStatus.SUCCEEDED,
        ]:
            automation_context.mark_run_success(
                "WARNING: Automate assumed a success status,"
                " but it was not marked as so by the function."
            )
    except Exception:
        trace = traceback.format_exc()
        print(trace)
        automation_context.mark_run_failed(
            "Function error. Check the automation run logs for details."
        )
    finally:
        if not automation_context.context_view:
            automation_context.set_context_view()
        automation_context.report_run_status()
        return automation_context
