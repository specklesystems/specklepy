from typing import Literal

from pydantic import Field

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class GenerateFileUploadUrlInput(GraphQLBaseModel):
    project_id: str
    file_name: str


class StartFileImportInput(GraphQLBaseModel):
    project_id: str
    model_id: str
    file_id: str
    etag: str


class FileImportResult(GraphQLBaseModel):
    duration_seconds: float
    download_duration_seconds: float
    parse_duration_seconds: float
    parser: str
    version_id: str | None


class FileImportInputBase(GraphQLBaseModel):
    project_id: str
    job_id: str
    warnings: list[str] = Field(default_factory=list)
    result: FileImportResult


class FileImportSuccessInput(FileImportInputBase):
    status: Literal["success"] = "success"


class FileImportErrorInput(FileImportInputBase):
    status: Literal["error"] = "error"
    reason: str


FinishFileImportInput = FileImportSuccessInput | FileImportErrorInput
