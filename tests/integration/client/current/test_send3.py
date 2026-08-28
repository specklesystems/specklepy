import time

import pytest

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.inputs.model_inputs import CreateModelInput
from specklepy.api.inputs.project_inputs import ProjectCreateInput
from specklepy.api.models.current import Model, Project, ProjectVisibility
from specklepy.bundle import BundleBuilder, Producer
from specklepy.objects.geometry.mesh import Mesh
from tests.integration.conftest import is_public


@pytest.mark.run()
@pytest.mark.skipif(is_public(), reason="The public API does not support these tests")
class TestSend3:
    @pytest.fixture
    def project(self, client: SpeckleClient) -> Project:
        return client.project.create(
            ProjectCreateInput(
                name="send3", description=None, visibility=ProjectVisibility.PUBLIC
            )
        )

    @pytest.fixture
    def model(self, client: SpeckleClient, project: Project) -> Model:
        return client.model.create(
            CreateModelInput(name="send3", description=None, project_id=project.id)
        )

    def test_send3_then_receive3_round_trips(
        self, client: SpeckleClient, project: Project, model: Model
    ):
        b = BundleBuilder(Producer("pytest", "0.0.0"), "m")
        walls = b.get_or_add_container_path(["Level 1", "Walls"], subtype="Category")
        concrete = b.get_or_add_material(
            "concrete", "Concrete", -8355712, roughness=0.8
        )
        l1 = b.get_or_add_level("L1", "Level 1", 0.0)
        wall = b.get_or_add_object("wall-1").set_properties(
            {"Constraints": {"Base Offset": 0.5}, "Identity Data": {"Mark": "W-01"}},
            name="Basic Wall",
            speckle_type="Objects.Data.DataObject",
            source_type="Walls",
        )
        wall.collection = walls
        wall.add_geometry(
            Mesh(vertices=[0, 0, 0, 1, 0, 0, 0, 1, 0], faces=[3, 0, 1, 2], units="m")
        ).material = concrete
        wall.level = l1
        door = b.get_or_add_object("door-1").set_properties({"Width": 0.9}, name="Door")
        door.collection = walls
        door.host = wall
        door.parent = wall
        b.add_model_property("projectInformation.number", 42.0)

        sent = operations.send3(client.account, project.id, model.id, b)
        assert (sent.project_id, sent.model_id, sent.object_count) == (
            project.id,
            model.id,
            2,
        )
        assert sent.version_id

        deadline = time.time() + 60
        version = None
        while time.time() < deadline and version is None:
            try:
                version = client.version.get(sent.version_id, project.id)
            except Exception:
                time.sleep(0.5)
        assert version is not None
        assert version.referenced_object == sent.bundle_reference

        with operations.receive3(
            client.account, project.id, model.id, sent.version_id
        ) as received:
            assert received.units == "m" and len(received.objects) == 2
            wall_r = received.object_by_application_id("wall-1")
            assert wall_r is not None
            assert wall_r["Constraints.Base Offset"] == 0.5
            assert wall_r.collection_path == ["Level 1", "Walls"]
            assert wall_r.level is not None and wall_r.level.name == "Level 1"
            [mesh] = wall_r.geometries
            assert len(mesh.decode_mesh().vertices) == 9
            assert mesh.material is not None and mesh.material.name == "Concrete"
            door_r = received.object_by_application_id("door-1")
            assert door_r is not None and door_r.host is wall_r
            assert door_r.parent is wall_r
            assert received.properties["projectInformation.number"] == 42.0
