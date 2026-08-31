"""ImportJob relationship rails over a synthetic in-memory IFC (no geometry) —
exercises the branches the sample files don't cover: raw-class container subtypes,
IN_ROOM/BOUNDS/HOSTED_ON/IN_ASSEMBLY/IN_GROUP, directed vs undirected CONNECTS_TO,
system label folding, and the double-reachable-element policy."""

from __future__ import annotations

import duckdb
import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

from speckleifc.converter.node import MEP_SYSTEM_SUBTYPE  # noqa: E402
from speckleifc.importer import ImportJob  # noqa: E402
from specklepy.bundle import BundleBuilder, Producer  # noqa: E402
from specklepy.bundle.spec import NODE_KINDS, NodeKind, Rel  # noqa: E402

BASE = "syn"


class _NoProgress:
    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def _guid() -> str:
    return ifcopenshell.guid.new()


GUIDS: dict[str, str] = {}


def _named_guid(label: str) -> str:
    return GUIDS.setdefault(label, _guid())


def _synthetic_file():
    f = ifcopenshell.file(schema="IFC4")
    proj = f.create_entity(
        "IfcProject", GlobalId=_named_guid("project"), Name="Project"
    )
    si = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    proj.UnitsInContext = f.create_entity("IfcUnitAssignment", Units=[si])

    site = f.create_entity("IfcSite", GlobalId=_named_guid("site"), Name="Site")
    storey = f.create_entity(
        "IfcBuildingStorey",
        GlobalId=_named_guid("storey"),
        Name="L1",
        Elevation=3.0,
    )
    f.create_entity(
        "IfcRelAggregates",
        GlobalId=_guid(),
        RelatingObject=proj,
        RelatedObjects=[site],
    )
    f.create_entity(
        "IfcRelAggregates",
        GlobalId=_guid(),
        RelatingObject=site,
        RelatedObjects=[storey],
    )

    wall = f.create_entity("IfcWall", GlobalId=_named_guid("wall"), Name="Wall")
    door = f.create_entity("IfcDoor", GlobalId=_named_guid("door"), Name="Door")
    assembly = f.create_entity(
        "IfcElementAssembly", GlobalId=_named_guid("assembly"), Name="Truss"
    )
    member = f.create_entity("IfcMember", GlobalId=_named_guid("member"), Name="Chord")
    f.create_entity(
        "IfcRelAggregates",
        GlobalId=_guid(),
        RelatingObject=assembly,
        RelatedObjects=[member],
    )

    space = f.create_entity("IfcSpace", GlobalId=_named_guid("space"), Name="Room")
    f.create_entity(
        "IfcRelAggregates",
        GlobalId=_guid(),
        RelatingObject=storey,
        RelatedObjects=[space],
    )
    chair = f.create_entity(
        "IfcFurnishingElement", GlobalId=_named_guid("chair"), Name="Chair"
    )
    f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=_guid(),
        RelatingStructure=space,
        RelatedElements=[chair],
    )

    pipe_a = f.create_entity(
        "IfcFlowSegment", GlobalId=_named_guid("pipe_a"), Name="Pipe A"
    )
    pipe_b = f.create_entity(
        "IfcFlowSegment", GlobalId=_named_guid("pipe_b"), Name="Pipe B"
    )
    pipe_x = f.create_entity(
        "IfcFlowSegment", GlobalId=_named_guid("pipe_x"), Name="Pipe X"
    )
    pipe_y = f.create_entity(
        "IfcFlowSegment", GlobalId=_named_guid("pipe_y"), Name="Pipe Y"
    )

    f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=_guid(),
        RelatingStructure=storey,
        RelatedElements=[wall, door, assembly, pipe_a, pipe_b, pipe_x, pipe_y],
    )
    # the wall is deliberately reachable twice (storey containment + space
    # containment) — the importer must keep the first conversion and not crash
    f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=_guid(),
        RelatingStructure=space,
        RelatedElements=[wall],
    )

    # hosting: wall ← opening ← door
    opening = f.create_entity("IfcOpeningElement", GlobalId=_named_guid("opening"))
    f.create_entity(
        "IfcRelVoidsElement",
        GlobalId=_guid(),
        RelatingBuildingElement=wall,
        RelatedOpeningElement=opening,
    )
    f.create_entity(
        "IfcRelFillsElement",
        GlobalId=_guid(),
        RelatingOpeningElement=opening,
        RelatedBuildingElement=door,
    )

    # space boundary: wall bounds the room
    f.create_entity(
        "IfcRelSpaceBoundary",
        GlobalId=_guid(),
        RelatingSpace=space,
        RelatedBuildingElement=wall,
    )

    # group: wall in a plain IfcGroup
    group = f.create_entity("IfcGroup", GlobalId=_named_guid("group"), Name="G1")
    f.create_entity(
        "IfcRelAssignsToGroup",
        GlobalId=_guid(),
        RelatedObjects=[wall],
        RelatingGroup=group,
    )

    # systems: predefined type folded into the label; name == type must not repeat
    hvac = f.create_entity(
        "IfcDistributionSystem",
        GlobalId=_named_guid("hvac"),
        Name="HVAC",
        PredefinedType="AIRCONDITIONING",
    )
    f.create_entity(
        "IfcRelAssignsToGroup",
        GlobalId=_guid(),
        RelatedObjects=[pipe_a, pipe_b],
        RelatingGroup=hvac,
    )
    pwc = f.create_entity(
        "IfcDistributionSystem",
        GlobalId=_named_guid("pwc"),
        Name="S_PWC",
        ObjectType="S_PWC",
    )
    # pipe_a belongs to both systems — multi-system membership must survive
    f.create_entity(
        "IfcRelAssignsToGroup",
        GlobalId=_guid(),
        RelatedObjects=[pipe_x, pipe_a],
        RelatingGroup=pwc,
    )

    # ports: a→b directed (SOURCE→SINK), x↔y undirected (SOURCEANDSINK)
    def _port(owner, flow, label):
        port = f.create_entity(
            "IfcDistributionPort", GlobalId=_named_guid(label), FlowDirection=flow
        )
        f.create_entity(
            "IfcRelNests",
            GlobalId=_guid(),
            RelatingObject=owner,
            RelatedObjects=[port],
        )
        return port

    f.create_entity(
        "IfcRelConnectsPorts",
        GlobalId=_guid(),
        RelatingPort=_port(pipe_a, "SOURCE", "port_a"),
        RelatedPort=_port(pipe_b, "SINK", "port_b"),
    )
    f.create_entity(
        "IfcRelConnectsPorts",
        GlobalId=_guid(),
        RelatingPort=_port(pipe_x, "SOURCEANDSINK", "port_x"),
        RelatedPort=_port(pipe_y, "SOURCEANDSINK", "port_y"),
    )
    return f


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("synthetic"))
    builder = BundleBuilder(Producer("ifc", "0.8.5"), "m", out, BASE)
    job = ImportJob(_synthetic_file(), builder, _NoProgress())
    job._convert_and_emit()  # no geometry in the synthetic file — skip the pre-pass
    builder.build()

    con = duckdb.connect()
    g = f"read_parquet('{out}/{BASE}"

    def k_of(label: str) -> int:
        return con.execute(
            f"SELECT object_index FROM {g}.eav.objects.parquet') "
            "WHERE application_id = ?",
            [GUIDS[label]],
        ).fetchone()[0]

    rels = set(
        con.execute(
            f"SELECT rel, src, dst FROM {g}.envelope.relations.parquet')"
        ).fetchall()
    )
    return con, g, k_of, rels


def test_containers_keep_raw_ifc_class_subtypes(bundle):
    con, g, _, _ = bundle
    containers = {
        name: (subtype, def_ref)
        for name, subtype, def_ref in con.execute(
            f"SELECT name, subtype, def_ref FROM {g}.envelope.nodes.parquet') "
            f"WHERE kind = {int(NodeKind.CONTAINER)}"
        ).fetchall()
    }
    assert containers["Project"][0] == "IfcProject"
    assert containers["Site"][0] == "IfcSite"
    assert containers["L1"][0] == "IfcBuildingStorey"
    assert containers["Room"][0] == "IfcSpace"
    # parent chain: Site's parent is the Project container
    project_k = con.execute(
        f"SELECT id FROM {g}.envelope.nodes.parquet') WHERE name = 'Project'"
    ).fetchone()[0]
    assert containers["Site"][1] == project_k


def test_scene_tree_and_level(bundle):
    con, g, k_of, rels = bundle
    wall = k_of("wall")
    in_collection = [r for r in rels if r[0] == int(Rel.IN_COLLECTION) and r[1] == wall]
    assert len(in_collection) == 1  # double-reachable wall converted exactly once

    level = con.execute(
        f"SELECT id, elevation FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.LEVEL)}"
    ).fetchall()
    assert len(level) == 1 and level[0][1] == 3.0
    assert (int(Rel.ON_LEVEL), wall, level[0][0]) in rels

    # the storey's own object row sits inside its own container, not on a level
    storey = k_of("storey")
    assert not any(r[0] == int(Rel.ON_LEVEL) and r[1] == storey for r in rels)


def test_assembly_rails(bundle):
    _, _, k_of, rels = bundle
    assembly, member = k_of("assembly"), k_of("member")
    assert (int(Rel.SUBELEMENT), assembly, member) in rels
    assert (int(Rel.IN_ASSEMBLY), member, assembly) in rels


def test_hosting_and_space_rails(bundle):
    _, _, k_of, rels = bundle
    wall, door, space, chair = k_of("wall"), k_of("door"), k_of("space"), k_of("chair")
    assert (int(Rel.HOSTED_ON), door, wall) in rels
    assert (int(Rel.BOUNDS), wall, space) in rels
    assert (int(Rel.IN_ROOM), chair, space) in rels


def test_group_rail(bundle):
    con, g, k_of, rels = bundle
    group_rows = con.execute(
        f"SELECT id, name FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.CONTAINER)} AND subtype = 'Group'"
    ).fetchall()
    assert [r[1] for r in group_rows] == ["G1"]
    assert (int(Rel.IN_GROUP), k_of("wall"), group_rows[0][0]) in rels


def test_system_labels_and_membership(bundle):
    con, g, k_of, rels = bundle
    # the exporter's subtype tag is a catalogued CONTAINER vocabulary value
    container_row = next(r for r in NODE_KINDS if r.id == int(NodeKind.CONTAINER))
    assert MEP_SYSTEM_SUBTYPE in (container_row.subtype_values or "").split(",")

    sysrows = con.execute(
        f"SELECT id, name FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.CONTAINER)} AND subtype = ?",
        [MEP_SYSTEM_SUBTYPE],
    ).fetchall()
    assert {r[1] for r in sysrows} == {"HVAC (AIRCONDITIONING)", "S_PWC"}

    sys_k = {name: k for k, name in sysrows}
    member_edges = {(src, dst) for r, src, dst in rels if r == int(Rel.IN_SYSTEM)}
    # pipe_a is in both systems — one IN_SYSTEM edge per membership
    assert member_edges == {
        (k_of("pipe_a"), sys_k["HVAC (AIRCONDITIONING)"]),
        (k_of("pipe_b"), sys_k["HVAC (AIRCONDITIONING)"]),
        (k_of("pipe_x"), sys_k["S_PWC"]),
        (k_of("pipe_a"), sys_k["S_PWC"]),
    }


def test_connections(bundle):
    _, _, k_of, rels = bundle
    a, b = k_of("pipe_a"), k_of("pipe_b")
    x, y = k_of("pipe_x"), k_of("pipe_y")
    assert (int(Rel.CONNECTS_TO), a, b) in rels
    assert (int(Rel.CONNECTS_TO), b, a) not in rels
    assert (int(Rel.CONNECTS_TO), x, y) in rels and (int(Rel.CONNECTS_TO), y, x) in rels


def test_eav_context_properties(bundle):
    con, g, _, _ = bundle
    rows = con.execute(
        f"""
        SELECT o.application_id, p.path, e.value_string
        FROM {g}.eav.eav.parquet') e
        JOIN {g}.eav.paths.parquet') p USING (path_index)
        JOIN {g}.eav.objects.parquet') o USING (object_index)
        WHERE p.path IN ('properties.Building Storey', 'ifcType',
                         'properties.parentApplicationId')
        """
    ).fetchall()
    by_obj = {}
    for app_id, path, value in rows:
        by_obj.setdefault(app_id, {})[path] = value
    wall = by_obj[GUIDS["wall"]]
    assert wall["ifcType"] == "IfcWall"
    assert wall["properties.Building Storey"] == "L1"
    # the assembly member records its product parent
    member = by_obj[GUIDS["member"]]
    assert member["properties.parentApplicationId"] == GUIDS["assembly"]


def test_default_scene_view(bundle):
    con, g, _, _ = bundle
    sv = con.execute(
        f"SELECT ord, source, ref FROM {g}.envelope.scene_views.parquet') "
        "WHERE is_default ORDER BY view, ord"
    ).fetchall()
    assert sv == [(0, "rel", str(int(Rel.ON_LEVEL))), (1, "eav", "ifcType")]


def test_baseline_model_placement_rows(bundle):
    con, g, _, _ = bundle
    rows = dict(
        con.execute(
            f"SELECT path, coalesce(value_string, CAST(value_boolean AS VARCHAR)) "
            f"FROM {g}.eav.model.parquet')"
        ).fetchall()
    )
    assert rows["modelPlacement.default"] == "internalOrigin"
    assert rows["modelPlacement.units"] == "m"
    assert rows["modelPlacement.appliedToGeometry"] == "false"
    assert "modelPlacement.options.internalOrigin.transform" in rows
    # no georeferencing in the synthetic file → no CRS/anchor rows
    assert not any(p.startswith(("crs.", "geolocation.")) for p in rows)
