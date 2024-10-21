"""Function execution module.

Provides mechanisms to execute any function,
 that conforms to the AutomateFunction "interface"
"""

import json
import sys
import traceback
from pathlib import Path
from typing import Callable, Optional, Tuple, TypeVar, Union, overload
from enum import Enum

from pydantic import create_model
from pydantic.json_schema import GenerateJsonSchema

from speckle_automate.automation_context import AutomationContext
from speckle_automate.schema import AutomateBase, AutomationRunData, AutomationStatus

T = TypeVar("T", bound=AutomateBase)

AutomateFunction = Callable[[AutomationContext, T], None]
AutomateFunctionWithoutInputs = Callable[[AutomationContext], None]


def _read_input_data(inputs_location: str) -> str:
    input_path = Path(inputs_location)
    if not input_path.exists():
        raise ValueError(f"Cannot find the function inputs file at {input_path}")

    return input_path.read_text()


def _parse_input_data(
    input_location: str, input_schema: Optional[type[T]]
) -> Tuple[AutomationRunData, Optional[T], str]:
    input_json_string = _read_input_data(input_location)

    class FunctionRunData(AutomateBase):
        speckle_token: str
        automation_run_data: AutomationRunData
        function_inputs: None = None

    parser_model = FunctionRunData

    if input_schema:
        parser_model = create_model(
            "FunctionRunDataWithInputs",
            function_inputs=(input_schema, ...),
            __base__=FunctionRunData,
        )

    input_data = parser_model.model_validate_json(input_json_string)
    return (
        input_data.automation_run_data,
        input_data.function_inputs,
        input_data.speckle_token,
    )


@overload
def execute_automate_function(
    automate_function: AutomateFunction[T],
    input_schema: type[T],
) -> None:
    ...


@overload
def execute_automate_function(
    automate_function: AutomateFunctionWithoutInputs,
) -> None:
    ...
 

def execute_automate_function(
    automate_function: Union[AutomateFunction[T], AutomateFunctionWithoutInputs],
    input_schema: Optional[type[T]] = None,
):
    """Runs the provided automate function with the input schema."""
    # first arg is the python file name, we do not need that
    args = sys.argv[1:]

    if len(args) != 2:
        raise ValueError("Incorrect number of arguments specified need 2")

    # we rely on a command name convention to decide what to do.
    # this is here, so that the function authors do not see any of this
    command, argument = args

    if command == "generate_schema":
        path = Path(argument)
        schema = json.dumps(
            input_schema.model_json_schema(
                by_alias=True, schema_generator=AutomateGenerateJsonSchema
            )
            if input_schema
            else {}
        )
        path.write_text(schema)

    elif command == "run":
        automation_run_data, function_inputs, speckle_token = _parse_input_data(
            argument, input_schema
        )

        automation_context = AutomationContext.initialize(
            automation_run_data, speckle_token
        )

        if function_inputs:
            automation_context = run_function(
                automation_context,
                automate_function,  # type: ignore
                function_inputs,  # type: ignore
            )

        else:
            automation_context = AutomationContext.initialize(
                automation_run_data, speckle_token
            )
            automation_context = run_function(
                automation_context,
                automate_function,  # type: ignore
            )

        # if we've gotten this far, the execution should technically be completed as expected
        # thus exiting with 0 is the schemantically correct thing to do
        exit_code = (
            1 if automation_context.run_status == AutomationStatus.EXCEPTION else 0
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
            AutomationStatus.EXCEPTION,
        ]:
            automation_context.mark_run_success(
                "WARNING: Automate assumed a success status,"
                " but it was not marked as so by the function."
            )
    except Exception:
        trace = traceback.format_exc()
        print(trace)
        automation_context.mark_run_exception(
            "Function error. Check the automation run logs for details."
        )
    finally:
        if not automation_context.context_view:
            automation_context.set_context_view()
        automation_context.report_run_status()
        return automation_context


class AutomateGenerateJsonSchema(GenerateJsonSchema):
    def __init__(self, by_alias: bool = True, ref_template: str = "#/$defs/{model}"):
        super().__init__(by_alias=by_alias, ref_template=ref_template)
        self.schema_dialect = "https://json-schema.org/draft/2020-12/schema"

    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)
        json_schema["$schema"] = self.schema_dialect

        if "properties" in json_schema:
            for prop, details in json_schema["properties"].items():
                self._process_property(
                    details, json_schema.get("$defs", {}), getattr(schema, prop, None)
                )

        if "$defs" in json_schema:
            for def_name, def_schema in json_schema["$defs"].items():
                self._process_property(def_schema, json_schema["$defs"], None)

        return json_schema

    def _process_property(self, property_schema, defs, field):
        if "allOf" in property_schema and len(property_schema["allOf"]) == 1:
            ref = property_schema["allOf"][0].get("$ref")
            if ref and ref.startswith("#/$defs/"):
                enum_name = ref.split("/")[-1]
                if enum_name in defs:
                    enum_schema = defs[enum_name]
                    property_schema.update(enum_schema)
                    del property_schema["allOf"]

        if "enum" in property_schema:
            enum_values = property_schema["enum"]
            property_schema["oneOf"] = [
                {"const": value, "title": str(value).upper()} for value in enum_values
            ]
            del property_schema["enum"]

        if isinstance(field, Enum):
            property_schema["oneOf"] = [
                {"const": item.value, "title": item.name} for item in field.__class__
            ]
            if "default" in property_schema:
                property_schema["default"] = property_schema["default"].value

        if "type" not in property_schema:
            if "oneOf" in property_schema:
                property_schema["type"] = "string"
            elif "default" in property_schema:
                property_schema["type"] = self._infer_type(property_schema["default"])
            else:
                property_schema["type"] = "object"

    @staticmethod
    def _infer_type(value):
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        else:
            return "object"
