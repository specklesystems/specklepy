"""IfcBundleExporter on a synthetic converted tree — exercises the proxy→envelope mapping,
especially the topology branches the real sample files don't cover (directed CONNECTS_TO,
IN_SYSTEM)."""

from __future__ import annotations

import duckdb

from speckleifc.bundle_exporter import IfcBundleExporter
from specklepy.bundle.spec import Rel
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
            f"SELECT object_index FROM {g}.eav.objects.parquet') WHERE application_id = ?",
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
        f"SELECT name, subtype FROM {g}.envelope.nodes.parquet') WHERE subtype = 'System'"
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

    # default scene view is Level (ON_LEVEL rel) > IFC class (ifcType eav), outermost-first
    sv = con.execute(
        f"SELECT ord, source, ref FROM {g}.envelope.scene_views.parquet') "
        "WHERE is_default ORDER BY view, ord"
    ).fetchall()
    assert sv == [(0, "rel", str(int(Rel.ON_LEVEL))), (1, "eav", "ifcType")]
