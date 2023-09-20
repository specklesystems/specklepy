"""This module provides an abstraction layer above the Speckle Automate runtime."""
from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Optional, Union

import httpx
from gql import gql
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport

from speckle_automate.schema import (
    AutomateBase,
    AutomationResult,
    AutomationRunData,
    AutomationStatus,
    ObjectResult,
    ObjectResultLevel,
)


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
                f"Could not autenticate to {automation_run_data.speckle_server_url}",
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

    def elapsed(self) -> float:
        """Return the elapsed time in seconds since the initialization time."""
        return time.perf_counter() - self._init_time

    def receive_version(self) -> Base:
        """Receive the Speckle project version that triggered this automation run."""
        commit = self.speckle_client.commit.get(
            self.automation_run_data.project_id, self.automation_run_data.version_id
        )
        if not commit.referencedObject:
            raise ValueError("The commit has no referencedObject, cannot receive it.")
        base = operations.receive(
            commit.referencedObject, self._server_transport, self._memory_transport
        )
        print(
            f"It took {self.elapsed():2f} seconds to receive",
            f" the speckle version {self.automation_run_data.version_id}",
        )
        return base

    def create_new_version_in_project(
        self, root_object: Base, model_id: str, version_message: str = ""
    ) -> None:
        """Save a base model to a new version on the project.

        Args:
            root_object (Base): The Speckle base object for the new version.
            model_id (str): For now please use a `branchName`!
            version_message (str): The message for the new version.
        """
        if model_id == self.automation_run_data.model_id:
            raise ValueError(
                f"The target model id: {model_id} cannot match the model id"
                f" that triggered this automation: {self.automation_run_data.model_id}"
            )

        root_object_id = operations.send(
            root_object,
            [self._server_transport, self._memory_transport],
            use_default_cache=False,
        )

        version_id = self.speckle_client.commit.create(
            stream_id=self.automation_run_data.project_id,
            object_id=root_object_id,
            branch_name=model_id,
            message=version_message,
            source_application="SpeckleAutomate",
        )
        self._automation_result.result_versions.append(version_id)

    def report_run_status(self) -> None:
        """Report the current run status to the project of this automation."""
        query = gql(
            """
            mutation ReportFunctionRunStatus(
                $automationId: String!, 
                $automationRevisionId: String!, 
                $automationRunId: String!,
                $versionId: String!,
                $functionId: String!,
                $runStatus: AutomationRunStatus!
                $elapsed: Float!
                $resultVersionIds: [String!]!
                $statusMessage: String
                $objectResults: JSONObject
            ){
                automationMutations {
                    functionRunStatusReport(input: {
                        automationId: $automationId
                        automationRevisionId: $automationRevisionId
                        automationRunId: $automationRunId
                        versionId: $versionId
                        functionRuns: [
                        {
                            functionId: $functionId
                            status: $runStatus,
                            elapsed: $elapsed,
                            resultVersionIds: $resultVersionIds,
                            statusMessage: $statusMessage
                            results: $objectResults
                        }]
                   })
                }
            }
            """
        )
        if self.run_status in [AutomationStatus.SUCCEEDED, AutomationStatus.FAILED]:
            object_results = {
                "version": "1.0.0",
                "values": {
                    "speckleObjects": self._automation_result.model_dump(by_alias=True)[
                        "objectResults"
                    ],
                    "blobs": self._automation_result.blobs,
                },
            }
        else:
            object_results = None
        params = {
            "automationId": self.automation_run_data.automation_id,
            "automationRevisionId": self.automation_run_data.automation_revision_id,
            "automationRunId": self.automation_run_data.automation_run_id,
            "versionId": self.automation_run_data.version_id,
            "functionId": self.automation_run_data.function_id,
            "runStatus": self.run_status.value,
            "statusMessage": self._automation_result.status_message,
            "elapsed": self.elapsed(),
            "resultVersionIds": self._automation_result.result_versions,
            "objectResults": object_results,
        }
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
        files = {path_obj.name: open(str(path_obj), "rb")}

        url = (
            f"{self.automation_run_data.speckle_server_url}/api/stream/"
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

        for upload_result in upload_response.upload_results:
            self._automation_result.blobs.append(upload_result.blob_id)

    def mark_run_failed(self, status_message: str) -> None:
        """Mark the current run a failure."""
        self._mark_run(AutomationStatus.FAILED, status_message)

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

        msg = f"Automation run {status.value} after {duration:2f} seconds."
        print("\n".join([msg, status_message]) if status_message else msg)

    def add_object_error(self, object_id: str, error_cause: str) -> None:
        """Add an error to a given Speckle object."""
        self._add_object_result(object_id, ObjectResultLevel.ERROR, error_cause)

    def add_object_warning(self, object_id: str, warning: str) -> None:
        """Add a warning to a given Speckle object."""
        self._add_object_result(object_id, ObjectResultLevel.WARNING, warning)

    def add_object_info(self, object_id: str, info: str) -> None:
        """Add an info message to a given Speckle object."""
        self._add_object_result(object_id, ObjectResultLevel.INFO, info)

    def _add_object_result(
        self, object_id: str, level: ObjectResultLevel, status_message: str
    ) -> None:
        print(
            f"Object {object_id} was marked with {level.value.upper()}",
            f" cause: {status_message}",
        )
        self._automation_result.object_results[object_id].append(
            ObjectResult(level=level, status_message=status_message)
        )
