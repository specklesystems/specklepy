"""This module provides an abstraction layer above the Speckle Automate runtime."""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from gql import gql

from speckle_automate.schema import (
    AutomateBase,
    AutomationResult,
    AutomationRunData,
    AutomationStatus,
    ObjectResultLevel,
    ResultCase,
)
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models.current import Model, Version
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport


@dataclass
class AutomationContext:
    """A context helper class.

    This class exposes methods to work with the Speckle Automate context inside
    Speckle Automate functions.

    An instance of AutomationContext is injected into every run of a function.
    """

    automation_run_data: AutomationRunData
    speckle_client: SpeckleClient
    _server_transport: ServerTransport
    _speckle_token: str

    #: keep a memory transponrt at hand, to speed up things if needed
    _memory_transport: MemoryTransport = field(default_factory=MemoryTransport)

    #: added for performance measuring
    _init_time: float = field(default_factory=time.perf_counter)
    _automation_result: AutomationResult = field(default_factory=AutomationResult)

    @classmethod
    def initialize(
        cls, automation_run_data: Union[str, AutomationRunData], speckle_token: str
    ) -> "AutomationContext":
        """Bootstrap the AutomateSDK from raw data.

        Todo:
        ----
            * bootstrap a structlog logger instance
            * expose a logger, that ppl can use instead of print
        """
        # parse the json value if its not an initialized project data instance
        automation_run_data = (
            automation_run_data
            if isinstance(automation_run_data, AutomationRunData)
            else AutomationRunData.model_validate_json(automation_run_data)
        )
        speckle_client = SpeckleClient(
            automation_run_data.speckle_server_url,
            automation_run_data.speckle_server_url.startswith("https"),
        )
        speckle_client.authenticate_with_token(speckle_token)
        if not speckle_client.account:
            msg = (
                f"Could not authenticate to {automation_run_data.speckle_server_url}",
                "with the provided token",
            )
            raise ValueError(msg)
        server_transport = ServerTransport(
            automation_run_data.project_id, speckle_client
        )
        return cls(automation_run_data, speckle_client, server_transport, speckle_token)

    @property
    def run_status(self) -> AutomationStatus:
        """Get the status of the automation run."""
        return self._automation_result.run_status

    @property
    def status_message(self) -> Optional[str]:
        """Get the current status message."""
        return self._automation_result.status_message

    def elapsed(self) -> float:
        """Return the elapsed time in seconds since the initialization time."""
        return time.perf_counter() - self._init_time

    def receive_version(self) -> Base:
        """Receive the Speckle project version that triggered this automation run."""
        # TODO: this is a quick hack to keep implementation consistency.
        # Move to proper receive many versions
        version_id = self.automation_run_data.triggers[0].payload.version_id
        try:
            version = self.speckle_client.version.get(
                version_id, self.automation_run_data.project_id
            )
        except SpeckleException as err:
            raise ValueError(
                f"""Could not receive specified version.
                Is your environment configured correctly?
                project_id: {self.automation_run_data.project_id}
                model_id: {self.automation_run_data.triggers[0].payload.model_id}
                version_id: {self.automation_run_data.triggers[0].payload.version_id}
                """
            ) from err

        if not version.referenced_object:
            raise Exception(
                "This version is past the version history limit,",
                " cannot execute an automation on it",
            )

        base = operations.receive(
            version.referenced_object, self._server_transport, self._memory_transport
        )
        # self._closure_tree = base["__closure"]
        print(
            f"It took {self.elapsed():.2f} seconds to receive",
            f" the speckle version {version_id}",
        )
        return base

    def create_new_model_in_project(
        self, model_name: str, model_description: Optional[str] = None
    ) -> Model:
        input = CreateModelInput(
            name=model_name,
            description=model_description,
            project_id=self.automation_run_data.project_id,
        )

        return self.speckle_client.model.create(input)

    def get_model(self, model_id: str) -> Model:
        """
        Args:
            model_id (str): The id of the model to get
        """
        return self.speckle_client.model.get(
            model_id, self.automation_run_data.project_id
        )

    def create_new_version_in_project(
        self, root_object: Base, model_id: str, version_message: str = ""
    ) -> Version:
        """Save a base model to a new version on the project.

        Args:
            root_object (Base): The Speckle base object for the new version.
            model_id (str): Id of model to create the new version on.
            version_message (str): The message for the new version.
        """

        matching_trigger = [
            t
            for t in self.automation_run_data.triggers
            if t.payload.model_id == model_id
        ]
        if matching_trigger:
            raise ValueError(
                f"The target model: {model_id} cannot match the model"
                f" that triggered this automation:"
                f" {matching_trigger[0].payload.model_id}"
            )

        root_object_id = operations.send(
            root_object,
            [self._server_transport, self._memory_transport],
            use_default_cache=False,
        )

        create_version_input = CreateVersionInput(
            object_id=root_object_id,
            model_id=model_id,
            project_id=self.automation_run_data.project_id,
            message=version_message,
            source_application="SpeckleAutomate",
        )
        version = self.speckle_client.version.create(create_version_input)

        self._automation_result.result_versions.append(version.id)
        return version

    @property
    def context_view(self) -> Optional[str]:
        return self._automation_result.result_view

    def set_context_view(
        self,
        # f"{model_id}@{version_id} or {model_id} "
        resource_ids: Optional[List[str]] = None,
        include_source_model_version: bool = True,
    ) -> None:
        link_resources = (
            [
                f"{t.payload.model_id}@{t.payload.version_id}"
                for t in self.automation_run_data.triggers
            ]
            if include_source_model_version
            else []
        )
        if resource_ids:
            link_resources.extend(resource_ids)
        if not link_resources:
            raise Exception(
                "We do not have enough resource ids to compose a context view"
            )
        self._automation_result.result_view = (
            f"/projects/{self.automation_run_data.project_id}"
            f"/models/{','.join(link_resources)}"
        )

    def report_run_status(self) -> None:
        """Report the current run status to the project of this automation."""
        query = gql(
            """
            mutation AutomateFunctionRunStatusReport(
                $projectId: String!
                $functionRunId: String!
                $status: AutomateRunStatus!
                $statusMessage: String
                $results: JSONObject
                $contextView: String
            ){
                automateFunctionRunStatusReport(input: {
                    projectId: $projectId
                    functionRunId: $functionRunId
                    status: $status
                    statusMessage: $statusMessage
                    contextView: $contextView
                    results: $results
                })
            }
        """
        )
        if self.run_status in [AutomationStatus.SUCCEEDED, AutomationStatus.FAILED]:
            object_results = {
                "version": 2,
                "values": {
                    "objectResults": self._automation_result.model_dump(by_alias=True)[
                        "objectResults"
                    ],
                    "blobIds": self._automation_result.blobs,
                },
            }
        else:
            object_results = None

        params = {
            "projectId": self.automation_run_data.project_id,
            "functionRunId": self.automation_run_data.function_run_id,
            "status": self.run_status.value,
            "statusMessage": self._automation_result.status_message,
            "results": object_results,
            "contextView": self._automation_result.result_view,
        }
        print(f"Reporting run status with content: {params}")
        self.speckle_client.httpclient.execute(query, params)

    def store_file_result(self, file_path: Union[Path, str]) -> None:
        """Save a file attached to the project of this automation."""
        path_obj = (
            Path(file_path).resolve() if isinstance(file_path, str) else file_path
        )

        class UploadResult(AutomateBase):
            blob_id: str
            file_name: str
            upload_status: int

        class BlobUploadResponse(AutomateBase):
            upload_results: list[UploadResult]

        if not path_obj.exists():
            raise ValueError("The given file path doesn't exist")

        files = {path_obj.name: path_obj.open("rb")}

        url = (
            f"{self.automation_run_data.speckle_server_url}api/stream/"
            f"{self.automation_run_data.project_id}/blob"
        )
        data = (
            httpx.post(
                url,
                files=files,
                headers={"authorization": f"Bearer {self._speckle_token}"},
            )
            .raise_for_status()
            .json()
        )

        upload_response = BlobUploadResponse.model_validate(data)

        if len(upload_response.upload_results) != 1:
            raise ValueError("Expecting one upload result.")

        self._automation_result.blobs.extend(
            [upload_result.blob_id for upload_result in upload_response.upload_results]
        )

    def mark_run_failed(self, status_message: str) -> None:
        """Mark the current run a failure."""
        self._mark_run(AutomationStatus.FAILED, status_message)

    def mark_run_exception(self, status_message: str) -> None:
        """Mark the current run a failure."""
        self._mark_run(AutomationStatus.EXCEPTION, status_message)

    def mark_run_success(self, status_message: Optional[str]) -> None:
        """Mark the current run a success with an optional message."""
        self._mark_run(AutomationStatus.SUCCEEDED, status_message)

    def _mark_run(
        self, status: AutomationStatus, status_message: Optional[str]
    ) -> None:
        duration = self.elapsed()
        self._automation_result.status_message = status_message
        self._automation_result.run_status = status
        self._automation_result.elapsed = duration

        msg = f"Automation run {status.value} after {duration:.2f} seconds."
        print("\n".join([msg, status_message]) if status_message else msg)

    def attach_error_to_objects(
        self,
        category: str,
        affected_objects: Union[Base, List[Base]],
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visual_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new error case to the run results.
        Args:
            category (str): A short tag for the event type.
            affected_objects (Union[Base, List[Base]]): A single object or a list of
                objects that are causing the error case.
            message (Optional[str]): Optional message.
            metadata: User provided metadata key value pairs
            visual_overrides: Case specific 3D visual overrides.
        """
        self.attach_result_to_objects(
            ObjectResultLevel.ERROR,
            category,
            affected_objects,
            message,
            metadata,
            visual_overrides,
        )

    def attach_warning_to_objects(
        self,
        category: str,
        affected_objects: Union[Base, List[Base]],
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visual_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new warning case to the run results.

        Args:
            category (str): A short tag for the event type.
            affected_objects (Union[Base, List[Base]]): A single object or a list of
                objects that are causing the warning case.
            message (Optional[str]): Optional message.
            metadata: User provided metadata key value pairs
            visual_overrides: Case specific 3D visual overrides.
        """
        self.attach_result_to_objects(
            ObjectResultLevel.WARNING,
            category,
            affected_objects,
            message,
            metadata,
            visual_overrides,
        )

    def attach_success_to_objects(
        self,
        category: str,
        affected_objects: Union[Base, List[Base]],
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visual_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new success case to the run results.

        Args:
            category (str): A short tag for the event type.
            affected_objects (Union[Base, List[Base]]): A single object or a list of
                objects that are causing the success case.
            message (Optional[str]): Optional message.
            metadata: User provided metadata key value pairs
            visual_overrides: Case specific 3D visual overrides.
        """
        self.attach_result_to_objects(
            ObjectResultLevel.SUCCESS,
            category,
            affected_objects,
            message,
            metadata,
            visual_overrides,
        )

    def attach_info_to_objects(
        self,
        category: str,
        affected_objects: Union[Base, List[Base]],
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visual_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new info case to the run results.

        Args:
            category (str): A short tag for the event type.
            affected_objects (Union[Base, List[Base]]): A single object or a list of
                objects that are causing the info case.
            message (Optional[str]): Optional message.
            metadata: User provided metadata key value pairs
            visual_overrides: Case specific 3D visual overrides.
        """
        self.attach_result_to_objects(
            ObjectResultLevel.INFO,
            category,
            affected_objects,
            message,
            metadata,
            visual_overrides,
        )

    def attach_result_to_objects(
        self,
        level: ObjectResultLevel,
        category: str,
        affected_objects: Union[Base, List[Base]],
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visual_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new result case to the run results.

        Args:
            level: Result level.
            category (str): A short tag for the event type.
            affected_objects (Union[Base, List[Base]]): A single object or a list of
                objects that are causing the info case.
            message (Optional[str]): Optional message.
            metadata: User provided metadata key value pairs
            visual_overrides: Case specific 3D visual overrides.
        """
        if isinstance(affected_objects, list):
            if len(affected_objects) < 1:
                raise ValueError(
                    f"Need atleast one object to report a(n) {level.value.upper()}"
                )
            object_list = affected_objects
        else:
            object_list = [affected_objects]

        ids: Dict[str, Optional[str]] = {}
        for o in object_list:
            # validate that the Base.id is not None. If its a None, throw an Exception
            if not o.id:
                raise Exception(
                    f"You can only attach {level} results to objects with an id."
                )
            ids[o.id] = o.applicationId
        print(
            f"Created new {level.value.upper()}"
            f" category: {category} caused by: {message}"
        )
        self._automation_result.object_results.append(
            ResultCase(
                category=category,
                level=level,
                object_app_ids=ids,
                message=message,
                metadata=metadata,
                visual_overrides=visual_overrides,
            )
        )
