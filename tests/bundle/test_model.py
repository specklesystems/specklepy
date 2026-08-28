import os

import pytest

from specklepy.bundle.bundle_reader import read_bundle
from specklepy.bundle.model import (
    GeometryRole,
    Model,
    ModelContainer,
    ModelDefinition,
    ModelInstance,
    ModelLevel,
    ModelMaterial,
)
from specklepy.bundle.spec import NodeKind, Rel
from tests.bundle import fixture_bundle

BASE = "fx"


def _model(out: str, geometry_downloaded: bool = True) -> Model:
    files = sorted(os.path.join(out, f) for f in os.listdir(out))
    return Model("p", "m", "v", out, files, read_bundle(out), geometry_downloaded)


@pytest.fixture
def model(tmp_path):
    out = str(tmp_path)
    ks = fixture_bundle.build(out, BASE)
    return _model(out), ks


def test_objects_expose_flat_path_keyed_properties(model):
    m, ks = model
    wall = m.object_by_application_id("wall-1")
    assert wall is not None and wall.k == ks.wall
    assert wall.name == "Wall-1"
    assert wall["Pset_Wall.Width"] == 200.0
    assert wall.get_bool("Pset_Wall.LoadBearing") is True
    assert wall["ifcType"] == "IfcWall"  # root-scalar fallback
    assert wall["nope"] is None
    assert dict(wall.properties) == {
        "Pset_Wall.Width": 200.0,
        "Pset_Wall.LoadBearing": True,
    }
    assert "name" in wall.root_properties and "name" not in wall.properties
    assert len(wall.type_properties) == 0
    assert m.property_paths == ["Pset_Wall.Width", "Pset_Wall.LoadBearing"]
    assert m.objects_with("Pset_Wall.Width") == [wall]
    assert [o.application_id for o in m.objects if o.get_double("Pset_Wall.Width")] == [
        "wall-1"
    ]


def test_geometries_load_lazily_and_carry_placements(model):
    m, ks = model
    assert not m.is_geometry_loaded
    wall = m.object(ks.wall)
    geometries = wall.geometries
    assert m.is_geometry_loaded
    assert [(g.k, g.role, g.ord, g.transform) for g in geometries] == [
        (ks.mesh_geo, GeometryRole.DISPLAY, 0, None),
        (ks.region_geo, GeometryRole.DISPLAY, 1, None),
        (ks.text_geo, GeometryRole.DISPLAY, 2, None),
    ]
    assert geometries[0].decode_mesh().vertices[:3] == [0.0, 0.0, 0.0]
    assert geometries[2].decode().value == "Hi"

    placed = m.object(ks.placed)
    by_k = {g.k: g for g in placed.geometries}
    assert set(by_k) == {ks.mesh_geo + 3, ks.mesh_geo + 4}
    assert by_k[ks.mesh_geo + 3].placement.k == ks.instance
    assert by_k[ks.mesh_geo + 4].placement.k == ks.nested_instance
    assert by_k[ks.mesh_geo + 3].transform == fixture_bundle.IDENTITY
    assert m.object(ks.host).geometries == []


def test_geometry_not_downloaded_raises(tmp_path):
    out = str(tmp_path)
    fixture_bundle.build(out, BASE)
    m = _model(out, geometry_downloaded=False)
    with pytest.raises(RuntimeError, match="include_geometry"):
        _ = m.geometries


def test_close_deletes_files_but_data_stays(model):
    m, ks = model
    with m:
        assert os.path.exists(m.directory)
    assert not os.path.exists(m.directory)
    assert len(m.objects) == 6
    with pytest.raises(RuntimeError, match="closed"):
        _ = m.object(ks.wall).geometries


def test_relationships_object_to_object(model):
    m, ks = model
    wall, host = m.object(ks.wall), m.object(ks.host)
    assert wall.children == [host] and host.parent == wall
    assert host.host == wall and wall.hosted == [host]
    assert wall.bounds_rooms == [host] and host.bounded_by == [wall]
    assert wall.room == host and host.contains == [wall]
    assert host.assembly == wall and wall.assembly_members == [host]
    assert wall.connected_to == [host] and host.connected_to == [wall]


def test_relationships_object_to_node(model):
    m, ks = model
    wall = m.object(ks.wall)
    assert isinstance(wall.level, ModelLevel)
    assert (wall.level.name, wall.level.elevation, wall.level.kind) == (
        "L1",
        3.0,
        NodeKind.LEVEL,
    )
    assert wall.level.objects == [wall]
    assert wall.system.subtype == "MEP System"
    assert [g.name for g in wall.groups] == ["Group A"]
    assert isinstance(wall.collection, ModelContainer)
    assert wall.collection.subtype == "Layer" and wall.collection.gh_topology == "0-1"
    assert wall.collection.objects == [wall] and wall.collection.path == ["Walls"]
    assert m.levels == [wall.level]
    assert len(m.collections) == 4  # layer, model, system, group


def test_appearance_three_planes(model):
    m, ks = model
    wall = m.object(ks.wall)
    mesh = wall.geometries[0]
    assert isinstance(mesh.material, ModelMaterial)
    assert mesh.material.name == "Painted Steel" and mesh.material.ior == 1.45
    assert mesh.color.argb == -65536
    assert wall.material is mesh.material and wall.color is mesh.color
    assert wall.collection.material is mesh.material
    assert wall.collection.color is mesh.color
    assert mesh.effective_material is mesh.material
    assert mesh.effective_color is wall.color
    region = wall.geometries[1]
    assert region.material is None and region.effective_material is wall.material
    assert region.effective_color is wall.color
    assert len(m.materials) == 2 and len(m.colors) == 1


def test_instancing(model):
    m, ks = model
    placed = m.object(ks.placed)
    [placement] = placed.placements
    assert isinstance(placement, ModelInstance)
    assert placement.transform == fixture_bundle.IDENTITY
    assert isinstance(placement.definition, ModelDefinition)
    assert placement.definition.name == "WallBody"
    assert placed.definition is placement.definition
    assert placement.definition.placements == [placement]
    assert placement.definition.objects == [placed]
    assert [o.application_id for o in placement.definition.members] == [
        "member-1",
        "nested-member-1",
    ]
    nested = m.object(ks.nested_member)
    assert [p.k for p in nested.placements] == [ks.nested_instance]
    assert nested.definition.name == "Bolt"
    assert m.object(ks.wall).definition is None


def test_scene_view_tiers_and_segments(model):
    m, ks = model
    [tier] = m.default_scene_view
    assert tier.is_relation and tier.relation == int(Rel.ON_LEVEL)
    wall = m.object(ks.wall)
    assert wall.collection_path == ["L1"]
    [segment] = wall.scene_view_segments
    assert segment.name == "L1" and segment.node is wall.level
    assert m.object(ks.host).scene_view_segments == []
    assert m.unknown_relations == set()


def test_model_level_data(model):
    m, _ = model
    assert m.properties["modelPlacement.default"] == "projectBasePoint"
    assert m.properties["projectInformation.name"] == "Fixture"
    assert [c.name for c in m.camera_views] == ["Front"]
    assert [f.field_name for f in m.property_set_definitions] == [
        "Width",
        "LoadBearing",
    ]
    assert m.units == ""
