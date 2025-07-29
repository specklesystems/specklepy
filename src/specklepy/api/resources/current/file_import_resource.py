from pathlib import Path

from typing_extensions import override

from specklepy.core.api.inputs import (
    FinishFileImportInput,
    GenerateFileUploadUrlInput,
    StartFileImportInput,
)
from specklepy.core.api.models import FileImport, FileUploadUrl
from specklepy.core.api.models.current import ResourceCollection
from specklepy.core.api.resources import FileImportResource as CoreResource
from specklepy.core.api.resources.current.file_import_resource import UploadFileResponse
from specklepy.logging import metrics


class FileImportResource(CoreResource):
    """API Access class for projects"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

    @override
    def start_file_import(self, input: StartFileImportInput) -> FileImport:
        metrics.track(metrics.SDK, self.account, {"name": "File Import Start"})
        return super().start_file_import(input)

    @override
    def generate_upload_url(self, input: GenerateFileUploadUrlInput) -> FileUploadUrl:
        """
        Get a file upload url from the Speckle server.

        This method asks the server to create a pre-signed S3 url,
        which can be used as a short term authenticated route,
        to put a file to the server.
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "File Import Generate Upload Url"}
        )
        return super().generate_upload_url(input)

    @override
    def upload_file(self, file: Path, url: str) -> UploadFileResponse:
        """
        Uploads a file to the given S3 url.

        This method should be used together with the generate_upload_url method,
        which generates a pre-signed S3 url, that can be used to upload the file to.
        """
        metrics.track(metrics.SDK, self.account, {"name": "File Import Upload File"})
        return super().upload_file(file, url)

    @override
    def download_file(self, project_id: str, file_id: str, target_file: Path) -> Path:
        """Download a file blob attached to the project, to the target path."""
        metrics.track(metrics.SDK, self.account, {"name": "File Import Download File"})
        return super().download_file(project_id, file_id, target_file)

    @override
    def finish_file_import_job(self, input: FinishFileImportInput) -> bool:
        """
        This is mostly an internal api, that marks a file import job finished.

        Only use this if you are writing a file importer, that is responsible for
        processing file import jobs.
        """
        metrics.track(metrics.SDK, self.account, {"name": "File Import Finish Job"})
        return super().finish_file_import_job(input)

    @override
    def get_model_file_import_jobs(
        self,
        *,
        project_id: str,
        model_id: str,
        limit: int = 25,
        cursor: str | None = None,
    ) -> ResourceCollection[FileImport]:
        metrics.track(metrics.SDK, self.account, {"name": "File Import Get Model Jobs"})
        return super().get_model_file_import_jobs(
            project_id=project_id, model_id=model_id, limit=limit, cursor=cursor
        )
