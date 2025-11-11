from pathlib import Path

import pytest

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.inputs.file_import_inputs import (
    FileImportErrorInput,
    FileImportResult,
    FileImportSuccessInput,
    GenerateFileUploadUrlInput,
    StartFileImportInput,
)
from specklepy.core.api.inputs.model_inputs import CreateModelInput
from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
from specklepy.core.api.models import Project
from specklepy.core.api.models.current import FileUploadUrl
from specklepy.core.helpers import crypto_random_string
from specklepy.transports.server.server import ServerTransport
from tests.integration.fakemesh import FakeMesh


class TestFileImportResource:
    @pytest.fixture
    def file_path(self) -> Path:
        path = Path("./tests/integration/client/current/test_file.ifc").absolute()
        assert path.exists()
        return path

    @pytest.fixture
    def project(self, client: SpeckleClient) -> Project:
        return client.project.create(
            ProjectCreateInput(
                name="test", description=None, visibility=ProjectVisibility.PRIVATE
            )
        )

    @pytest.fixture(scope="function")
    def upload_url(
        self, project: Project, file_path: Path, client: SpeckleClient
    ) -> FileUploadUrl:
        upload_url_result = client.file_import.generate_upload_url(
            GenerateFileUploadUrlInput(project_id=project.id, file_name=file_path.name)
        )
        return upload_url_result

    def test_generate_upload_url(self, upload_url: FileUploadUrl) -> None:
        assert upload_url.file_id
        assert upload_url.url

    def test_upload_file(
        self, file_path: Path, client: SpeckleClient, upload_url: FileUploadUrl
    ) -> None:
        response = client.file_import.upload_file(file=file_path, url=upload_url.url)
        assert response.etag

    def test_download_file(
        self,
        file_path: Path,
        client: SpeckleClient,
        project: Project,
        upload_url: FileUploadUrl,
    ) -> None:
        _ = client.file_import.upload_file(file=file_path, url=upload_url.url)

        target_file = file_path.parent.joinpath("download.ifc")

        downloaded_file = client.file_import.download_file(
            project_id=project.id, file_id=upload_url.file_id, target_file=target_file
        )

        assert downloaded_file.exists()

        assert file_path.stat().st_size == downloaded_file.stat().st_size

        downloaded_file.unlink()

    def test_start_file_import(
        self,
        file_path: Path,
        client: SpeckleClient,
        project: Project,
        upload_url: FileUploadUrl,
    ) -> None:
        model = client.model.create(
            CreateModelInput(name=crypto_random_string(10), project_id=project.id)
        )
        upload_response = client.file_import.upload_file(
            file=file_path, url=upload_url.url
        )
        response = client.file_import.start_file_import(
            StartFileImportInput(
                project_id=project.id,
                model_id=model.id,
                file_id=upload_url.file_id,
                etag=upload_response.etag,
            )
        )

        assert response.converted_status == 0
        assert response.converted_version_id is None

        upload_jobs = client.file_import.get_model_file_import_jobs(
            project_id=project.id,
            model_id=model.id,
        )

        assert upload_jobs.total_count == 1
        job = upload_jobs.items[0]
        assert job
        assert job.converted_status == 0
        assert job.converted_version_id is None

    def test_finish_file_import_success(
        self,
        file_path: Path,
        client: SpeckleClient,
        project: Project,
        upload_url: FileUploadUrl,
        mesh: FakeMesh,
    ) -> None:
        model = client.model.create(
            CreateModelInput(name=crypto_random_string(10), project_id=project.id)
        )
        upload_response = client.file_import.upload_file(
            file=file_path, url=upload_url.url
        )
        job_response = client.file_import.start_file_import(
            StartFileImportInput(
                project_id=project.id,
                model_id=model.id,
                file_id=upload_url.file_id,
                etag=upload_response.etag,
            )
        )

        assert job_response.converted_status == 0
        assert job_response.converted_version_id is None

        upload_jobs = client.file_import.get_model_file_import_jobs(
            project_id=project.id,
            model_id=model.id,
        )

        assert upload_jobs.total_count == 1
        job = upload_jobs.items[0]
        assert job
        assert job.converted_status == 0
        assert job.converted_version_id is None

        transport = ServerTransport(client=client, stream_id=project.id)
        hash = operations.send(mesh, transports=[transport])

        version = client.version.create(
            input=CreateVersionInput(
                project_id=project.id, model_id=model.id, object_id=hash
            )
        )

        finish_result = client.file_import.finish_file_import_job(
            input=FileImportSuccessInput(
                project_id=project.id,
                job_id=job_response.id,
                result=FileImportResult(
                    download_duration_seconds=0,
                    duration_seconds=0,
                    parse_duration_seconds=0,
                    parser="test",
                    version_id=version.id,
                ),
            )
        )

        assert finish_result

        upload_jobs = client.file_import.get_model_file_import_jobs(
            project_id=project.id,
            model_id=model.id,
        )

        assert upload_jobs.total_count == 1
        job = upload_jobs.items[0]
        assert job
        assert job.converted_status == 2
        assert job.converted_version_id == version.id

    def test_finish_file_import_error(
        self,
        file_path: Path,
        client: SpeckleClient,
        project: Project,
        upload_url: FileUploadUrl,
    ) -> None:
        model = client.model.create(
            CreateModelInput(name=crypto_random_string(10), project_id=project.id)
        )
        upload_response = client.file_import.upload_file(
            file=file_path, url=upload_url.url
        )
        job_response = client.file_import.start_file_import(
            StartFileImportInput(
                project_id=project.id,
                model_id=model.id,
                file_id=upload_url.file_id,
                etag=upload_response.etag,
            )
        )

        assert job_response.converted_status == 0
        assert job_response.converted_version_id is None

        upload_jobs = client.file_import.get_model_file_import_jobs(
            project_id=project.id,
            model_id=model.id,
        )

        assert upload_jobs.total_count == 1
        job = upload_jobs.items[0]
        assert job
        assert job.converted_status == 0
        assert job.converted_version_id is None

        finish_result = client.file_import.finish_file_import_job(
            input=FileImportErrorInput(
                project_id=project.id,
                job_id=job_response.id,
                reason="Test error",
                result=FileImportResult(
                    download_duration_seconds=0,
                    duration_seconds=0,
                    parse_duration_seconds=0,
                    parser="test",
                    version_id=None,
                ),
            )
        )

        assert finish_result

        upload_jobs = client.file_import.get_model_file_import_jobs(
            project_id=project.id,
            model_id=model.id,
        )

        assert upload_jobs.total_count == 1
        job = upload_jobs.items[0]
        assert job
        assert job.converted_status == 3
        assert job.converted_version_id is None
