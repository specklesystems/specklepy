"""IfcBundleExporter on a synthetic converted tree — exercises the proxy→envelope
mapping, especially the topology branches the real sample files don't cover
(directed CONNECTS_TO, IN_SYSTEM)."""

from __future__ import annotations

import duckdb

from speckleifc.bundle_exporter import COLLECTION_SUBTYPE, IfcBundleExporter
from specklepy.bundle.spec import NODE_KINDS, NodeKind, Rel
from specklepy.objects.data_objects import DataObject
from specklepy.objects.geometry.mesh import Mesh
from specklepy.objects.models.collections.collection import Collection
from specklepy.objects.other import RenderMaterial
from specklepy.objects.proxies import (
    ConnectionProxy,
    InstanceDefinitionProxy,
    InstanceProxy,
    LevelProxy,
    RenderMaterialProxy,
    SystemProxy,
)

BASE = "syn"


def _build_tree() -> Collection:
    mesh = Mesh(vertices=[0, 0, 0, 1, 0, 0, 0, 1, 0], faces=[3, 0, 1, 2], units="m")
    mesh.applicationId = "mesh-1"

    wall = DataObject(
        applicationId="wall-guid",
        name="Wall",
        properties={"Pset": {"Width": 200}},
        displayValue=[
            InstanceProxy(
                units="m",
                definitionId="DEFINITION:mesh-1",
                transform=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                maxDepth=0,
                applicationId="wall:DEF",
            )
        ],
    )
    wall["ifcType"] = "IfcWall"
    wall["@elements"] = []

    root = Collection(applicationId="proj", name="Project", elements=[wall])
    root["ifcType"] = "IfcProject"
    root.elements.append(Collection(name="definitionGeometry", elements=[mesh]))

    root["instanceDefinitionProxies"] = [
        InstanceDefinitionProxy(
            applicationId="DEFINITION:mesh-1",
            name="def",
            objects=["mesh-1"],
            maxDepth=0,
        )
    ]
    root["renderMaterialProxies"] = [
        RenderMaterialProxy(
            objects=["mesh-1"],
            value=RenderMaterial(
                applicationId="mat-1", name="Steel", diffuse=0xFFAABBCC, opacity=1.0
            ),
        )
    ]
    level = DataObject(
        applicationId="L1",
        name="Level 1",
        properties={"Attributes": {"Elevation": 3.0}},
        displayValue=[],
    )
    root["levelProxies"] = [
        LevelProxy(objects=["wall-guid"], value=level, applicationId="L1")
    ]
    root["systemProxies"] = [
        SystemProxy(
            objects=["wall-guid"],
            name="HVAC",
            applicationId="sys-1",
            systemType="AIRCONDITIONING",
        )
    ]
    root["connectionProxies"] = [
        ConnectionProxy(
            sourceAppId="a",
            targetAppId="b",
            applicationId="c1",
            sourceFlowDirection="SOURCE",
            targetFlowDirection="SINK",
        ),
        ConnectionProxy(
            sourceAppId="x",
            targetAppId="y",
            applicationId="c2",
            sourceFlowDirection="SOURCEANDSINK",
            targetFlowDirection="SOURCEANDSINK",
        ),
    ]
    return root


def test_exporter_maps_full_tree(tmp_path):
    out = str(tmp_path)
    root_id, obj_count = IfcBundleExporter(out, BASE).export(_build_tree())
    assert root_id == "proj"

    con = duckdb.connect()
    g = f"read_parquet('{out}/{BASE}"

    def k_of(app_id):
        return con.execute(
            f"SELECT object_index FROM {g}.eav.objects.parquet') "
            "WHERE application_id = ?",
            [app_id],
        ).fetchone()[0]

    rels = set(
        con.execute(
            f"SELECT rel, src, dst FROM {g}.envelope.relations.parquet')"
        ).fetchall()
    )

    # geometry + definition + material wiring
    assert (
        con.execute(f"SELECT count(*) FROM {g}.geometries.parquet')").fetchone()[0] == 1
    )
    assert any(r[0] == int(Rel.DEFINES) for r in rels)
    assert any(r[0] == int(Rel.HAS_MATERIAL) for r in rels)
    assert any(r[0] == int(Rel.DISPLAY_INSTANCE) for r in rels)

    # wall is IN_COLLECTION of the project; ON_LEVEL L1; IN_SYSTEM sys-1
    wall_k = k_of("wall-guid")
    assert any(r[0] == int(Rel.IN_COLLECTION) and r[1] == wall_k for r in rels)
    assert any(r[0] == int(Rel.ON_LEVEL) and r[1] == wall_k for r in rels)
    assert any(r[0] == int(Rel.IN_SYSTEM) and r[1] == wall_k for r in rels)

    # system container: subtype canonical "System", IFC type folded into name
    sysrow = con.execute(
        f"SELECT name, subtype FROM {g}.envelope.nodes.parquet') "
        "WHERE subtype = 'System'"
    ).fetchone()
    assert sysrow[1] == "System"
    assert "AIRCONDITIONING" in sysrow[0]

    # directed connection a->b is a SINGLE edge; undirected x<->y is a reciprocal pair
    a, b, x, y = k_of("a"), k_of("b"), k_of("x"), k_of("y")
    assert (int(Rel.CONNECTS_TO), a, b) in rels
    assert (int(Rel.CONNECTS_TO), b, a) not in rels
    assert (int(Rel.CONNECTS_TO), x, y) in rels and (int(Rel.CONNECTS_TO), y, x) in rels

    # level node carries elevation
    elev = con.execute(
        f"SELECT elevation FROM {g}.envelope.nodes.parquet') WHERE kind = 5"
    ).fetchone()[0]
    assert elev == 3.0

    # ARGB stored as signed int32 (0xFFAABBCC -> negative)
    argb = con.execute(
        f"SELECT argb FROM {g}.envelope.nodes.parquet') WHERE kind = 3"
    ).fetchone()[0]
    assert argb == 0xFFAABBCC - 0x1_0000_0000

    # default scene view is Level (ON_LEVEL rel) > IFC class (ifcType eav),
    # outermost-first
    sv = con.execute(
        f"SELECT ord, source, ref FROM {g}.envelope.scene_views.parquet') "
        "WHERE is_default ORDER BY view, ord"
    ).fetchall()
    assert sv == [(0, "rel", str(int(Rel.ON_LEVEL))), (1, "eav", "ifcType")]


def _spatial_twin(guid: str, name: str, ifc_type: str) -> DataObject:
    """The converter emits every spatial element as a Collection wrapping a twin
    DataObject with the same GUID (spatial_element_converter)."""
    twin = DataObject(applicationId=guid, name=name, properties={}, displayValue=[])
    twin["ifcType"] = ifc_type
    twin["@elements"] = []
    return twin


def _build_spatial_tree() -> Collection:
    """Project > Site > Building > Storey > Space (+ a desk contained in the
    space), shaped exactly as the converter emits it (ENG-9180)."""
    desk = DataObject(
        applicationId="desk-guid", name="Desk", properties={}, displayValue=[]
    )
    desk["ifcType"] = "IfcFurniture"
    desk["@elements"] = []

    space = Collection(
        applicationId="space-guid",
        name="Kitchen",
        elements=[_spatial_twin("space-guid", "Kitchen", "IfcSpace"), desk],
    )
    space["ifcType"] = "IfcSpace"

    storey = Collection(
        applicationId="storey-guid",
        name="Ground Floor",
        elements=[
            _spatial_twin("storey-guid", "Ground Floor", "IfcBuildingStorey"),
            space,
        ],
    )
    storey["ifcType"] = "IfcBuildingStorey"

    building = Collection(
        applicationId="building-guid",
        name="Building",
        elements=[_spatial_twin("building-guid", "Building", "IfcBuilding"), storey],
    )
    building["ifcType"] = "IfcBuilding"

    site = Collection(
        applicationId="site-guid",
        name="Site",
        elements=[_spatial_twin("site-guid", "Site", "IfcSite"), building],
    )
    site["ifcType"] = "IfcSite"

    root = Collection(applicationId="proj", name="Project", elements=[site])
    root["ifcType"] = "IfcProject"
    root.elements.append(Collection(name="definitionGeometry", elements=[]))
    return root


def test_spatial_hierarchy_uses_canonical_containers(tmp_path):
    """ENG-9180: spatial containers carry the catalogued Collection subtype, spaces
    ship as objects only, and the IFC class survives as the ifcType eav row."""
    out = str(tmp_path)
    root_id, _ = IfcBundleExporter(out, "spatial").export(_build_spatial_tree())
    assert root_id == "proj"

    con = duckdb.connect()
    g = f"read_parquet('{out}/spatial"

    def k_of(app_id):
        return con.execute(
            f"SELECT object_index FROM {g}.eav.objects.parquet') "
            "WHERE application_id = ?",
            [app_id],
        ).fetchone()[0]

    def ifc_type_of(app_id):
        return con.execute(
            f"SELECT e.value_string FROM {g}.eav.eav.parquet') e "
            f"JOIN {g}.eav.paths.parquet') p USING (path_index) "
            f"JOIN {g}.eav.objects.parquet') o USING (object_index) "
            "WHERE p.path = 'ifcType' AND o.application_id = ?",
            [app_id],
        ).fetchone()[0]

    containers = con.execute(
        f"SELECT id, name, subtype, def_ref FROM {g}.envelope.nodes.parquet') "
        f"WHERE kind = {int(NodeKind.CONTAINER)}"
    ).fetchall()

    # project/site/building/storey mint containers; the space does NOT
    assert {r[1] for r in containers} == {"Project", "Site", "Building", "Ground Floor"}

    # every emitted subtype is the canonical tag, and that tag is catalogued in the
    # declared bundle vocabulary — never an IFC class name
    assert {r[2] for r in containers} == {COLLECTION_SUBTYPE}
    container_kind = next(r for r in NODE_KINDS if r.id == int(NodeKind.CONTAINER))
    assert COLLECTION_SUBTYPE in container_kind.subtype_values.split(",")

    # the def_ref parent chain IS the spatial hierarchy
    by_name = {r[1]: r for r in containers}
    assert by_name["Project"][3] is None
    assert by_name["Site"][3] == by_name["Project"][0]
    assert by_name["Building"][3] == by_name["Site"][0]
    assert by_name["Ground Floor"][3] == by_name["Building"][0]

    # spatial twins are objects with the IFC class preserved as eav
    for guid, ifc_type in [
        ("site-guid", "IfcSite"),
        ("building-guid", "IfcBuilding"),
        ("storey-guid", "IfcBuildingStorey"),
        ("space-guid", "IfcSpace"),
        ("desk-guid", "IfcFurniture"),
    ]:
        assert ifc_type_of(guid) == ifc_type

    rels = set(
        con.execute(
            f"SELECT rel, src, dst FROM {g}.envelope.relations.parquet')"
        ).fetchall()
    )
    storey_k = by_name["Ground Floor"][0]
    space_k, desk_k = k_of("space-guid"), k_of("desk-guid")

    # the space object and its contents both attach to the storey container...
    assert (int(Rel.IN_COLLECTION), space_k, storey_k) in rels
    assert (int(Rel.IN_COLLECTION), desk_k, storey_k) in rels

    # ...and occupancy rides as IN_ROOM: desk -> space object, exactly once; the
    # space itself is in no room
    in_room = [r for r in rels if r[0] == int(Rel.IN_ROOM)]
    assert in_room == [(int(Rel.IN_ROOM), desk_k, space_k)]
