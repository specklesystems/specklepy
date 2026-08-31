import os

import pytest

from specklepy.bundle import BundleBuilder, Producer
from specklepy.bundle.bundle_reader import read_bundle
from specklepy.bundle.envelope_writer import CameraView, SceneViewKey
from specklepy.bundle.model import Model, ModelContainer, ModelLevel
from specklepy.bundle.spec import Rel
from specklepy.objects.geometry.mesh import Mesh

PRODUCER = Producer("test", "1.0")
T = [1, 0, 0, 10, 0, 1, 0, 20, 0, 0, 1, 0, 0, 0, 0, 1]


def tri(dx: float = 0.0) -> Mesh:
    return Mesh(
        vertices=[dx, 0.0, 0.0, dx + 1.0, 0.0, 0.0, dx, 1.0, 0.0],
        faces=[3, 0, 1, 2],
        units="m",
    )


def build_and_read(tmp_path, author) -> Model:
    out = str(tmp_path)
    with BundleBuilder(PRODUCER, "m", out) as b:
        author(b)
        files = b.build()
    assert all(os.path.basename(f).startswith("bundle.") for f in files.files)
    return Model("p", "m", "v", out, files.files, read_bundle(out))


def describe(b, app_id, collection=None, properties=None, **kwargs):
    obj = b.get_or_add_object(app_id)
    if properties is not None or kwargs:
        obj.set_properties(properties, **kwargs)
    if collection is not None:
        obj.collection = collection
    return obj


def test_solid_and_display_ordinals_count_per_relation(tmp_path):
    def author(b):
        o = describe(b, "o", b.get_or_add_container_path(["A"]), {})
        assert o.add_raw_geometry(b"3dm", "3dm").ord == 0
        assert o.add_geometry(tri()).ord == 0
        assert o.add_geometry(tri(1)).ord == 1

    m = build_and_read(tmp_path, author)
    roles = [(g.role.name, g.ord) for g in m.object_by_application_id("o").geometries]
    assert roles == [("DISPLAY", 0), ("SOLID", 0), ("DISPLAY", 1)]


def test_objects_properties_collections_roundtrip(tmp_path):
    def author(b):
        walls = b.get_or_add_container_path(["Level 1", "Walls"], subtype="Category")
        wall = describe(
            b,
            "wall-1",
            walls,
            {"Constraints": {"Base Offset": 0.5}, "Identity Data": {"Mark": "W-01"}},
            name="Basic Wall",
            speckle_type="Objects.Data.DataObject",
            source_type="Walls",
        )
        wall.add_geometry(tri())
        describe(b, "door-1", walls, {"Width": 0.9}, name="Door")
        assert b.get_or_add_object("wall-1") is wall

    m = build_and_read(tmp_path, author)
    assert m.units == "m" and len(m.objects) == 2
    wall = m.object_by_application_id("wall-1")
    assert wall.name == "Basic Wall"
    assert wall.get_double("Constraints.Base Offset") == 0.5
    assert wall.get_string("Identity Data.Mark") == "W-01"
    assert wall.get_string("speckle_type") == "Objects.Data.DataObject"
    assert wall.get_string("type") == "Walls"
    assert wall.collection_path == ["Level 1", "Walls"]
    assert wall.collection.subtype == "Category"
    assert wall.collection.parent.name == "Level 1"
    [tier] = m.default_scene_view
    assert tier.relation == int(Rel.IN_COLLECTION)
    [g] = wall.geometries
    assert len(g.decode_mesh().vertices) == 9
    assert m.object_by_application_id("door-1").geometries == []


def test_relations_and_appearance_roundtrip(tmp_path):
    def author(b):
        walls = b.get_or_add_container_path(["Walls"])
        concrete = b.get_or_add_material("m", "Concrete", -8355712, roughness=0.8)
        red = b.get_or_add_color(-65536)
        l1 = b.get_or_add_level("L1", "Level 1", 0.0)
        wall = describe(b, "wall", walls, {})
        wall.add_geometry(tri()).material = concrete
        wall.level = l1
        door = describe(b, "door", walls, {})
        door.color = red
        door.host = wall
        door.parent = wall
        room = describe(b, "room", walls, {})
        wall.bounds(room)
        door.room = room
        door.connect_to(wall)
        walls.color = red
        group = b.get_or_add_container("g", "Group A", None, "Group")
        wall.add_to_group(group)
        supply = b.get_or_add_semantic_container("s1", "Supply", None, "MEP System")
        ret = b.get_or_add_semantic_container("s2", "Return", None, "MEP System")
        wall.add_to_system(supply)
        wall.add_to_system(ret)
        assert b.get_or_add_material("m", "Concrete", -8355712) is concrete
        with pytest.raises(ValueError):
            b.get_or_add_material("m", "Other", -8355712)

    m = build_and_read(tmp_path, author)
    wall, door, room = (m.object_by_application_id(a) for a in ("wall", "door", "room"))
    [mesh] = wall.geometries
    assert mesh.material.name == "Concrete" and mesh.material.roughness == 0.8
    assert wall.material is None and mesh.effective_material is mesh.material
    assert door.color.argb == -65536 and mesh.effective_color is wall.collection.color
    assert isinstance(wall.level, ModelLevel) and wall.level.name == "Level 1"
    assert door.host is wall and wall.hosted == [door]
    assert door.parent is wall and wall.children == [door]
    assert wall.bounds_rooms == [room] and door.room is room
    assert door.connected_to == [wall] and wall.connected_to == [door]
    assert [g.name for g in wall.groups] == ["Group A"]
    assert [s.name for s in wall.systems] == ["Supply", "Return"]
    assert wall.system.name == "Supply"


def test_definitions_placements_members_roundtrip(tmp_path):
    def author(b):
        layer = b.get_or_add_container_path(["Blocks"], "Layer")
        fabric = b.get_or_add_material("fabric", "Fabric", 0)
        populated = []

        def populate(d):
            d.add_geometry(tri()).material = fabric
            populated.append(d)

        chair_def = b.get_or_add_definition("def-chair", "Chair", populate)
        describe(b, "chair-1", layer, name="Chair 1").place(chair_def, T)
        describe(b, "chair-2", layer, name="Chair 2").place(chair_def, T)
        assert b.get_or_add_definition("def-chair", None, populate) is chair_def
        assert len(populated) == 1
        with pytest.raises(ValueError):
            b.get_or_add_definition("def-chair", "x")

        table_def = b.get_or_add_definition("def-table", "Table")
        top = describe(b, "table-top", layer, {"material": "oak"}, name="Top")
        table_def.add_member(top, [tri(5)])
        describe(b, "table-1", layer, name="Table 1").place(table_def, T)

    m = build_and_read(tmp_path, author)
    chair1 = m.object_by_application_id("chair-1")
    [placement] = chair1.placements
    assert placement.transform[3] == 10
    assert chair1.definition.name == "Chair"
    assert len(chair1.definition.placements) == 2
    assert [o.application_id for o in chair1.definition.objects] == [
        "chair-1",
        "chair-2",
    ]
    [g] = chair1.geometries
    assert g.material.name == "Fabric" and g.transform is not None
    table = m.object_by_application_id("table-1")
    [top] = table.definition.members
    assert top.get_string("material") == "oak"
    assert m.object_by_application_id("table-top").geometries == []
    assert len(m.definitions) == 2


def test_model_extras_and_scene_view(tmp_path):
    def author(b):
        host = b.get_or_add_container("Main.rvt", "Main.rvt", None, "Model")
        l1 = b.get_or_add_level("L1", "Level 1", 0.0)
        o = describe(
            b,
            "w",
            None,
            {},
            name="W",
            root_scalars=[("category", "Walls"), ("family", "Basic")],
        )
        o.model = host
        o.level = l1
        b.scene_view(
            "Default",
            True,
            SceneViewKey.rel(Rel.IN_MODEL),
            SceneViewKey.rel(Rel.ON_LEVEL),
            SceneViewKey.eav("category"),
            SceneViewKey.eav("family"),
        )
        b.add_model_property("modelPlacement.units", "m")
        b.add_model_property("projectInformation.number", 42.0)
        b.add_camera_view(CameraView(0, "Front", True, 0, 0, -10, 5, 0, 1, 0, 0, 0, 1))

    m = build_and_read(tmp_path, author)
    w = m.object_by_application_id("w")
    assert len(m.default_scene_view) == 4
    assert [s.name for s in w.scene_view_segments] == [
        "Main.rvt",
        "Level 1",
        "Walls",
        "Basic",
    ]
    assert isinstance(w.scene_view_segments[0].node, ModelContainer)
    assert isinstance(w.scene_view_segments[1].node, ModelLevel)
    assert w.scene_view_segments[2].node is None
    assert m.properties["modelPlacement.units"] == "m"
    assert m.properties["projectInformation.number"] == 42.0
    assert [c.name for c in m.camera_views] == ["Front"]


def test_forward_reference_then_describe_writes_once(tmp_path):
    def author(b):
        later = b.get_or_add_object("later")
        assert not later.properties_written
        describe(b, "now", None, {}).connect_to(later)
        later.set_properties({"x": 1.0}, name="Later")
        with pytest.raises(RuntimeError):
            later.set_properties({}, name="Again")
        assert b.get_or_add_object("later") is later

    m = build_and_read(tmp_path, author)
    later = m.object_by_application_id("later")
    assert later.name == "Later" and later["x"] == 1.0
    assert m.object_by_application_id("now").connected_to == [later]


def test_children_explicit_ordinals_and_reparent_raises(tmp_path):
    def author(b):
        parent = describe(b, "p", None, {})
        a, c, d = (describe(b, n, None, {}) for n in "acd")
        parent.add_child(c, ord=2)
        parent.add_child(a, ord=0)
        d.parent = parent
        parent.add_child(a)  # idempotent
        other = describe(b, "other", None, {})
        with pytest.raises(RuntimeError):
            other.add_child(a)

    m = build_and_read(tmp_path, author)
    assert [c.application_id for c in m.object_by_application_id("p").children] == [
        "a",
        "c",
        "d",
    ]


def test_definition_members_render_only_through_placements(tmp_path):
    def author(b):
        layer = b.get_or_add_container_path(["Blocks"])
        bolt = b.get_or_add_definition("bolt", "Bolt")
        bolt.add_member(describe(b, "bolt-geo", layer, {}), [tri()])
        table = b.get_or_add_definition("table", "Table")
        top = describe(b, "top", layer, {})
        table.add_member(top, [tri(), tri(1)])
        leg = describe(b, "leg", layer, {})
        table.add_member_placement(leg, bolt, T)
        describe(b, "table-1", layer, {}).place(table, T)

    m = build_and_read(tmp_path, author)
    rels = m.bundle.relations
    top = m.object_by_application_id("top")
    assert rels.display_by_object(top.k) == [] and top.geometries == []
    assert rels.member_ord_by_definition[m.definitions[1].k] == [0, 1]
    leg = m.object_by_application_id("leg")
    assert [p.definition.name for p in leg.placements] == ["Bolt"]
    assert not any(e.src == leg.k for e in rels.display_instance_edges)
    placed = m.object_by_application_id("table-1")
    assert len(placed.geometries) == 3  # two top meshes + the nested bolt mesh
    assert all(g.transform is not None for g in placed.geometries)


def test_existing_geometry_shared_by_key(tmp_path):
    def author(b):
        o = describe(b, "o", None, {})
        g = o.add_geometry(tri(), geometry_key="mesh-A")
        assert b.try_get_geometry("mesh-A") is g
        d = b.get_or_add_definition("d", "D")
        d.add_existing_geometry(g)
        describe(b, "p", None, {}).place(d, T)

    m = build_and_read(tmp_path, author)
    assert len(m.geometries) == 1
    assert [g.k for g in m.object_by_application_id("p").geometries] == [0]


def test_gh_topology_only_on_the_leaf(tmp_path):
    def author(b):
        leaf = b.get_or_add_container_path(["Mesh", "Mesh"], gh_topology="{0;1}")
        describe(b, "o", leaf, {})

    m = build_and_read(tmp_path, author)
    o = m.object_by_application_id("o")
    assert o.collection.gh_topology == "{0;1}"
    assert o.collection.parent.gh_topology is None
    assert o.collection.parent.parent is None
    assert len(m.collections) == 2


def test_build_twice_raises_and_rename_rekeys_files(tmp_path):
    b = BundleBuilder(PRODUCER, "m", str(tmp_path))
    describe(b, "o", None, {})
    files = b.build()
    with pytest.raises(RuntimeError):
        b.build()
    renamed = files.rename_to("08de6a66ec")
    assert renamed.base_name == "08de6a66ec" and renamed.object_count == 1
    assert all(os.path.basename(f).startswith("08de6a66ec.") for f in renamed.files)
    assert all(os.path.exists(f) for f in renamed.files)
    assert len(renamed.by_name) == len(files.by_name)
    assert (
        files.rename_to("bundle") is files or renamed.rename_to("08de6a66ec") is renamed
    )


def test_type_key_dedups_type_parameters(tmp_path):
    def props():
        return {
            "Parameters": {
                "Constraints": {"Base Offset": {"name": "Base Offset", "value": 0.5}},
                "Type Parameters": {
                    "Construction": {"Width": {"name": "Width", "value": 0.2}}
                },
            }
        }

    def author(b):
        b.get_or_add_object("wall-1").set_properties(
            props(), name="Basic Wall", type_key="t"
        )
        b.get_or_add_object("wall-2").set_properties(
            props(), name="Basic Wall", type_key="t"
        )

    m = build_and_read(tmp_path, author)
    assert len(set(m.bundle.type_index_by_object.values())) == 1
    wall = m.object_by_application_id("wall-1")
    assert wall["Parameters.Type Parameters.Construction.Width"] == 0.2
    assert "Parameters.Type Parameters.Construction.Width" not in wall.properties
    assert wall.get_double("Parameters.Constraints.Base Offset") == 0.5


def test_assemblies_order_and_retraction(tmp_path):
    def author(b):
        asm = describe(b, "asm", None, {})
        m1, m2, m3 = (describe(b, n, None, {}) for n in ("m1", "m2", "m3"))
        asm.add_assembly_member(m2, ord=1)
        asm.add_assembly_member(m1, ord=0)
        asm.add_assembly_member(m3)
        asm.add_assembly_member(m1)  # idempotent
        with pytest.raises(RuntimeError):
            describe(b, "asm2", None, {}).add_assembly_member(m1)

    m = build_and_read(tmp_path, author)
    asm = m.object_by_application_id("asm")
    assert [o.application_id for o in asm.assembly_members] == ["m1", "m2", "m3"]
    assert m.object_by_application_id("m3").assembly is asm


def test_relation_cannot_be_retracted(tmp_path):
    with BundleBuilder(PRODUCER, "m", str(tmp_path)) as b:
        a = b.get_or_add_container_path(["A"])
        c = b.get_or_add_container_path(["C"])
        o = describe(b, "o", a, {})
        with pytest.raises(RuntimeError):
            o.collection = c
        o.collection = a  # idempotent
        with pytest.raises(RuntimeError):
            o.collection = None
        fresh = b.get_or_add_object("fresh")
        fresh.collection = None  # no edge yet → no-op
        fresh.collection = a
        assert fresh.collection is a


def test_meta_sdk_version_is_this_sdk(tmp_path):
    m = build_and_read(tmp_path, lambda b: describe(b, "o", None, {}))
    import duckdb

    row = duckdb.sql(
        f"SELECT sdk_name, sdk_version, produced_by FROM "
        f"read_parquet('{tmp_path}/bundle.envelope.meta.parquet')"
    ).fetchone()
    assert row == ("specklepy", Producer("x", "y").sdk_version, "test")
    assert "+" not in row[1] and m.units == "m"


def test_units_required():
    with pytest.raises(ValueError):
        BundleBuilder(PRODUCER, " ")
