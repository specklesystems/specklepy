import time

import pytest

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.inputs.model_ingestion_inputs import (
    ModelIngestionCreateInput,
    SourceDataInput,
)
from specklepy.api.inputs.model_inputs import CreateModelInput
from specklepy.api.inputs.project_inputs import ProjectCreateInput
from specklepy.api.models.current import (
    Model,
    ModelIngestion,
    Project,
    ProjectVisibility,
)
from specklepy.bundle.download import BundleReference
from specklepy.bundle.upload import ArtifactPipeline
from specklepy.objects.models.collections.collection import Collection
from specklepy.transports.server.server import ServerTransport
from tests.bundle import fixture_bundle
from tests.integration.conftest import is_public


@pytest.mark.run()
@pytest.mark.skipif(is_public(), reason="The public API does not support these tests")
class TestReceive3:
    @pytest.fixture
    def project(self, client: SpeckleClient) -> Project:
        return client.project.create(
            ProjectCreateInput(
                name="receive3", description=None, visibility=ProjectVisibility.PUBLIC
            )
        )

    @pytest.fixture
    def model(self, client: SpeckleClient, project: Project) -> Model:
        return client.model.create(
            CreateModelInput(name="receive3", description=None, project_id=project.id)
        )

    @pytest.fixture
    def ingestion(
        self, client: SpeckleClient, model: Model, project: Project
    ) -> ModelIngestion:
        return client.model_ingestion.create(
            ModelIngestionCreateInput(
                model_id=model.id,
                project_id=project.id,
                progress_message="uploading fixture bundle",
                source_data=SourceDataInput(
                    source_application_slug="pytest",
                    source_application_version="0.0.0",
                    file_name=None,
                    file_size_bytes=None,
                ),
            )
        )

    @pytest.fixture
    def version_id(
        self,
        client: SpeckleClient,
        project: Project,
        model: Model,
        ingestion: ModelIngestion,
        tmp_path,
    ) -> str:
        version_id = client.model_ingestion.get_reserved_version_id(
            project.id, ingestion.id
        )
        assert version_id, "server must reserve a version id for v2 uploads"
        fixture_bundle.build(str(tmp_path), version_id)
        with ArtifactPipeline(
            project.id, ingestion.id, version_id, client.account, str(tmp_path)
        ) as upload:
            upload.upload_dir(version_id, "wall-1", 6)
        deadline = time.time() + 60
        while time.time() < deadline:
            version = client.version.get(version_id, project.id)
            if BundleReference.is_reference(version.referenced_object):
                return version_id
            time.sleep(1)
        pytest.fail("version never advertised a bundle reference")

    def test_receive3_reads_the_uploaded_bundle(
        self, client: SpeckleClient, project: Project, model: Model, version_id: str
    ):
        with operations.receive3(client.account, project.id, model.id, version_id) as m:
            wall = m.object_by_application_id("wall-1")
            assert wall is not None and wall["Pset_Wall.Width"] == 200.0
            assert wall.level is not None and wall.level.name == "L1"
            assert [g.k for g in wall.geometries] == [0, 1, 2]
            material = wall.geometries[0].effective_material
            assert material is not None and material.name == "Painted Steel"
            assert m.properties["modelPlacement.default"] == "projectBasePoint"

    def test_legacy_receive_routes_bundle_references(
        self, client: SpeckleClient, project: Project, version_id: str
    ):
        version = client.version.get(version_id, project.id)
        assert version.referenced_object
        tree = operations.receive(
            version.referenced_object, ServerTransport(project.id, client)
        )
        assert isinstance(tree, Collection)
        assert tree["version"] == 4
        walls = tree.elements[0]
        assert isinstance(walls, Collection)
        assert [e.applicationId for e in walls.elements] == ["wall-1"]
