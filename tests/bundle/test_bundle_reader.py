import pytest

from specklepy.bundle.bundle_reader import read_bundle, read_geometries
from specklepy.bundle.spec import Rel
from tests.bundle import fixture_bundle

BASE = "fx"


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("bundle"))
    ks = fixture_bundle.build(out, BASE)
    return out, ks, read_bundle(out)


def test_objects_and_properties(bundle):
    _, ks, b = bundle
    assert b.object_app_ids[ks.wall] == "wall-1"
    assert len(b.object_app_ids) == 6
    assert b.property_table.get_double(ks.wall, "properties.Pset_Wall.Width") == 200.0
    assert b.property_table.get_string(ks.wall, "ifcType") == "IfcWall"
    assert b.type_index_by_object == {}
    assert len(b.type_properties(ks.wall)) == 0
    assert b.units == ""
    assert b.geometries == {}


def test_relations_are_bucketed(bundle):
    _, ks, b = bundle
    r = b.relations
    assert [e.dst for e in r.display_by_object(ks.wall)] == [
        ks.mesh_geo,
        ks.region_geo,
        ks.text_geo,
    ]
    assert r.object_by_geometry()[ks.mesh_geo] == ks.wall
    assert r.material_by_geometry[ks.mesh_geo] == ks.material
    assert r.color_by_geometry[ks.mesh_geo] == ks.color
    assert r.material_by_object[ks.wall] == ks.material
    assert r.color_by_object[ks.wall] == ks.color
    assert r.material_by_node[ks.layer] == ks.material
    assert r.color_by_node[ks.layer] == ks.color
    assert r.collection_by_object[ks.wall] == ks.layer
    assert r.groups_by_object[ks.wall] == [ks.group]
    assert r.places_by_object[ks.nested_member] == ks.nested_instance
    assert r.defines_by_definition[ks.definition] == [ks.mesh_geo + 3]
    assert r.defines_ord_by_definition[ks.definition] == [0]
    assert r.member_objects_by_definition[ks.definition] == [
        ks.member,
        ks.nested_member,
    ]
    assert r.member_ord_by_definition[ks.definition] == [0, 1]
    assert r.defines_instance_by_definition[ks.definition] == [ks.nested_instance]
    assert [(e.src, e.dst) for e in r.display_instance_edges] == [
        (ks.placed, ks.instance)
    ]
    assert [(e.src, e.dst) for e in r.subelement] == [(ks.wall, ks.host)]
    assert [(e.src, e.dst) for e in r.hosted_on] == [(ks.host, ks.wall)]
    assert [(e.src, e.dst) for e in r.in_assembly] == [(ks.host, ks.wall)]
    assert [(e.src, e.dst) for e in r.bounds] == [(ks.wall, ks.host)]
    assert [(e.src, e.dst) for e in r.in_room] == [(ks.wall, ks.host)]
    assert [(e.src, e.dst, e.ord) for e in r.connects_to] == [
        (ks.wall, ks.host, ks.system)
    ]
    by_rel = r.object_node_by_rel
    assert by_rel[int(Rel.ON_LEVEL)][ks.wall] == ks.level
    assert by_rel[int(Rel.IN_MODEL)][ks.wall] == ks.model
    assert by_rel[int(Rel.IN_SYSTEM)][ks.wall] == ks.system  # first membership
    assert r.systems_by_object[ks.wall] == [ks.system, ks.system2]
    assert r.unknown_rels == set()


def test_nodes(bundle):
    _, ks, b = bundle
    material = b.nodes[ks.material]
    assert (material.name, material.argb, material.emissive, material.ior) == (
        "Painted Steel",
        -1,
        -16711936,
        1.45,
    )
    assert b.nodes[ks.layer].subtype == "Layer"
    assert b.nodes[ks.layer].gh_topology == "0-1"
    assert b.nodes[ks.instance].def_ref == ks.definition
    assert b.nodes[ks.level].elevation == 3.0


def test_optional_tables(bundle):
    _, _, b = bundle
    assert [(t.source, t.ref) for t in b.default_scene_view] == [
        ("rel", str(int(Rel.ON_LEVEL)))
    ]
    assert [c.name for c in b.camera_views] == ["Front"]
    assert b.camera_views[0].fov == 45.0
    assert b.model_properties["modelPlacement.appliedToGeometry"] is True
    assert b.model_properties["modelPlacement.units"] == "m"
    assert [f.field_name for f in b.property_set_definitions] == [
        "Width",
        "LoadBearing",
    ]
    assert b.property_set_definitions[0].field_bucket_id == "bucket-w"


def test_geometries_read_from_shards(bundle):
    out, ks, _ = bundle
    geometries = read_geometries(out)
    assert set(geometries) == {0, 1, 2, 3, 4}
    assert geometries[ks.text_geo].type == "text"
    assert all(g.is_sgeo for g in geometries.values())
    assert read_bundle(out, load_geometry=True).geometries.keys() == geometries.keys()


def test_missing_required_table_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_bundle(str(tmp_path))
