from pathlib import Path
from typing import Any

import httpx
from gql import Client, gql

from specklepy.core.api.credentials import Account
from specklepy.core.api.inputs.file_import_inputs import (
    FinishFileImportInput,
    GenerateFileUploadUrlInput,
    StartFileImportInput,
)
from specklepy.core.api.models import FileImport, FileUploadUrl, ResourceCollection
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel
from specklepy.core.api.resource import ResourceBase
from specklepy.core.api.responses import DataResponse
from specklepy.logging.exceptions import SpeckleException


class UploadFileResponse(GraphQLBaseModel):
    etag: str


class FileImportResource(ResourceBase):
    """API Access class for project invites"""

    def __init__(
        self,
        account: Account,
        basepath: str,
        client: Client,
        server_version: tuple[Any, ...] | None,  # pyright: ignore[reportExplicitAny]
    ) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
            name="file-import",
        )

    def finish_file_import_job(self, input: FinishFileImportInput) -> bool:
        """
        This is mostly an internal api, that marks a file import job finished.

        Only use this if you are writing a file importer, that is responsible for
        processing file import jobs.
        """
        QUERY = gql(
            """
                mutation FinishFileImport($input: FinishFileImportInput!) {
                    data:fileUploadMutations {
                        data:finishFileImport(input: $input)
                    }
                }
            """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[bool]], QUERY, variables
        ).data.data

    def start_file_import(self, input: StartFileImportInput) -> FileImport:
        QUERY = gql(
            """
            mutation StartFileImport($input: StartFileImportInput!) {
                data:fileUploadMutations {
                    data:startFileImport(input: $input) {
                        id
                        projectId
                        convertedVersionId
                        userId
                        convertedStatus
                        convertedMessage
                        modelId
                        updatedAt
                    }
                }
            }
        """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[FileImport]], QUERY, variables
        ).data.data

    def generate_upload_url(self, input: GenerateFileUploadUrlInput) -> FileUploadUrl:
        """
        Get a file upload url from the Speckle server.

        This method asks the server to create a pre-signed S3 url,
        which can be used as a short term authenticated route,
        to put a file to the server.
        """
        QUERY = gql(
            """
            mutation GenerateUploadUrl($input: GenerateFileUploadUrlInput!) {
                data:fileUploadMutations {
                    data:generateUploadUrl(input: $input) {
                        fileId
                        url
                    }
                }
            }
        """
        )

        variables = {
            "input": input.model_dump(warnings="error", by_alias=True),
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[FileUploadUrl]], QUERY, variables
        ).data.data

    def upload_file(self, file: Path, url: str) -> UploadFileResponse:
        """
        Uploads a file to the given S3 url.

        This method should be used together with the generate_upload_url method,
        which generates a pre-signed S3 url, that can be used to upload the file to.
        """
        with open(file, "rb") as content:
            response = httpx.put(
                url,
                content=content,  # Pass file object directly for streaming
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file.stat().st_size),
                },
            ).raise_for_status()
            etag = response.headers.get("ETag", None)  # pyright: ignore[reportAny]
            if not etag:
                raise SpeckleException(
                    "Response does not have an ETag attached to it,"
                    + " cannot use this as an upload"
                )
            return UploadFileResponse(etag=str(etag))  # pyright: ignore[reportAny]

    def download_file(self, project_id: str, file_id: str, target_file: Path) -> Path:
        """Download a file blob attached to the project, to the target path."""
        if not target_file.parent.exists():
            target_file.parent.mkdir(parents=True)
        url = f"{self.basepath}/api/stream/{project_id}/blob/{file_id}"
        with httpx.stream(
            "GET", url, headers={"Authorization": f"Bearer {self.account.token}"}
        ) as response:
            _ = response.raise_for_status()
            with target_file.open("wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    _ = f.write(chunk)
        return target_file

    def get_model_file_import_jobs(
        self,
        *,
        project_id: str,
        model_id: str,
        limit: int = 25,
        cursor: str | None = None,
    ) -> ResourceCollection[FileImport]:
        QUERY = gql(
            """
            query ModelFileImportJobs(
                $projectId: String!,
                $modelId: String!,
                $input: GetModelUploadsInput
            ) {
              data:project(id: $projectId) {
                data:model(id: $modelId) {
                    data:uploads(input: $input) {
                        totalCount
                        cursor
                        items {
                            id
                            projectId
                            convertedVersionId
                            userId
                            convertedStatus
                            convertedMessage
                            modelId
                            updatedAt
                        }
                    }
                }
              }
            }
            """
        )

        variables = {
            "projectId": project_id,
            "modelId": model_id,
            "input": {
                "limit": limit,
                "cursor": cursor,
            },
        }

        return self.make_request_and_parse_response(
            DataResponse[DataResponse[DataResponse[ResourceCollection[FileImport]]]],
            QUERY,
            variables,
        ).data.data.data
