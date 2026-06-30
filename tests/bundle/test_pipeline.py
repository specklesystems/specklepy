"""End-to-end: drive ObjectsArtifactPipeline with a real Mesh + nodes/relations/props,
then read the whole bundle back with DuckDB."""

from __future__ import annotations

import duckdb

from specklepy.bundle.pipeline import ObjectsArtifactPipeline
from specklepy.bundle.spec import Rel
from specklepy.objects.geometry.mesh import Mesh

BASE = "model"


def _mesh() -> Mesh:
    # a single triangle
    return Mesh(
        vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        faces=[3, 0, 1, 2],
        units="m",
    )


def test_pipeline_full_bundle(tmp_path):
    out = str(tmp_path)
    with ObjectsArtifactPipeline(out, BASE) as p:
        obj_k = p.intern_object("element-1")
        p.add_properties(
            "element-1",
            {"Pset_Wall": {"Width": 200}},
            root_scalars=[("name", "Wall-1"), ("ifcType", "IfcWall")],
        )

        # definition holds the mesh; instance places it; object displays the instance.
        geo_k = p.add_geometry("mesh-1", _mesh())
        def_k = p.add_definition("def-1", "WallBody")
        p.defines(def_k, geo_k, 0)
        inst_k = p.add_instance(
            "place-1", def_k, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], "m"
        )
        p.display_instance(obj_k, inst_k, 0)

        mat_k = p.add_material(
            "mat-1", argb=-1, opacity=1.0, metalness=0.0, roughness=0.5
        )
        p.has_material(geo_k, mat_k)

        sys_k = p.add_container("sys-1", "Hot Water", None, "System")
        p.in_system(obj_k, sys_k, 0)
        p.connects_to(obj_k, obj_k)  # trivial self-edge just to exercise the rel

    con = duckdb.connect()
    g = f"read_parquet('{out}/{BASE}"

    # geometry landed with SGEO content + sha256 id
    geo = con.execute(
        f"SELECT geometryIndex, octet_length(content), type "
        f"FROM {g}.geometries.parquet')"
    ).fetchall()
    assert geo == [(geo_k, geo[0][1], "mesh")]
    assert geo[0][1] >= 16  # at least the SGEO header

    # the eav side has the object + its width + root scalars
    width = con.execute(
        f"""SELECT e.value_double FROM {g}.eav.eav.parquet') e
            JOIN {g}.eav.paths.parquet') pa USING(path_index)
            WHERE pa.path = 'properties.Pset_Wall.Width'"""
    ).fetchone()
    assert width[0] == 200.0
    names = con.execute(
        f"""SELECT e.value_string FROM {g}.eav.eav.parquet') e
            JOIN {g}.eav.paths.parquet') pa USING(path_index)
            WHERE pa.path = 'ifcType'"""
    ).fetchone()
    assert names[0] == "IfcWall"

    # envelope: the edges we emitted are present, with the right rel ids
    rels = set(
        con.execute(
            f"SELECT rel, src, dst FROM {g}.envelope.relations.parquet')"
        ).fetchall()
    )
    assert (int(Rel.DEFINES), def_k, geo_k) in rels
    assert (int(Rel.DISPLAY_INSTANCE), obj_k, inst_k) in rels
    assert (int(Rel.HAS_MATERIAL), geo_k, mat_k) in rels
    assert (int(Rel.IN_SYSTEM), obj_k, sys_k) in rels
    assert (int(Rel.CONNECTS_TO), obj_k, obj_k) in rels

    # the instance node carries its transform + units; the system container its subtype
    inst = con.execute(
        f"SELECT transform, units FROM {g}.envelope.nodes.parquet') WHERE id = {inst_k}"
    ).fetchone()
    assert inst[1] == "m" and inst[0].startswith("1.0,0.0")
    sub = con.execute(
        f"SELECT subtype, name FROM {g}.envelope.nodes.parquet') WHERE id = {sys_k}"
    ).fetchone()
    assert sub == ("System", "Hot Water")
