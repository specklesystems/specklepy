"""End-to-end: every ObjectsArtifactPipeline writer, read back via DuckDB."""

from __future__ import annotations

import os

import duckdb
import pytest

from specklepy.bundle import ObjectsArtifactPipeline, Producer
from specklepy.bundle.spec import SCHEMA_VERSION, NodeKind, Rel
from tests.bundle import fixture_bundle

BASE = "model"


@pytest.fixture
def bundle(tmp_path):
    out = str(tmp_path)
    ks = fixture_bundle.build(out, BASE)
    con = duckdb.connect()

    def q(sql: str):
        return con.execute(sql.replace("{g}", f"read_parquet('{out}/{BASE}")).fetchall()

    return out, ks, q


def test_meta_carries_producer_provenance(bundle):
    _, _, q = bundle
    assert q("SELECT * FROM {g}.envelope.meta.parquet')") == [
        (
            SCHEMA_VERSION,
            "fixture",
            "0.1",
            "specklepy",
            fixture_bundle.PRODUCER.sdk_version,
            None,
        )
    ]
    assert isinstance(SCHEMA_VERSION, str)


def test_geometries_land_with_type_labels(bundle):
    _, ks, q = bundle
    rows = dict(q("SELECT geometryIndex, type FROM {g}.geometries.parquet')"))
    assert rows[ks.mesh_geo] == "mesh"
    assert rows[ks.region_geo] == "region"
    assert rows[ks.text_geo] == "text"
    assert len(rows) == 5


def test_eav_rows(bundle):
    _, _, q = bundle
    rows = {
        path: (s, d, b)
        for path, s, d, b in q(
            """SELECT pa.path, e.value_string, e.value_double, e.value_boolean
               FROM {g}.eav.eav.parquet') e
               JOIN {g}.eav.paths.parquet') pa USING(path_index)"""
        )
    }
    assert rows["properties.Pset_Wall.Width"][1] == 200.0
    assert rows["properties.Pset_Wall.LoadBearing"][2] is True
    assert rows["ifcType"][0] == "IfcWall"


def test_every_relation_kind_is_emitted(bundle):
    _, ks, q = bundle
    rels = set(q("SELECT rel, src, dst, ord FROM {g}.envelope.relations.parquet')"))
    expected = {
        (Rel.DISPLAY, ks.wall, ks.mesh_geo, 0),
        (Rel.DISPLAY_INSTANCE, ks.placed, ks.instance, 0),
        (Rel.SUBELEMENT, ks.wall, ks.host, 0),
        (Rel.DEFINES, ks.definition, ks.mesh_geo + 3, 0),
        (Rel.DEFINES_INSTANCE, ks.definition, ks.nested_instance, 1),
        (Rel.DEFINES_MEMBER, ks.definition, ks.member, 0),
        (Rel.DEFINES_MEMBER, ks.definition, ks.nested_member, 1),
        (Rel.PLACES, ks.nested_member, ks.nested_instance, 0),
        (Rel.HAS_MATERIAL, ks.mesh_geo, ks.material, 0),
        (Rel.HAS_COLOR, ks.mesh_geo, ks.color, 0),
        (Rel.OBJECT_HAS_MATERIAL, ks.wall, ks.material, 0),
        (Rel.OBJECT_HAS_COLOR, ks.wall, ks.color, 0),
        (Rel.NODE_HAS_MATERIAL, ks.layer, ks.material, 0),
        (Rel.NODE_HAS_COLOR, ks.layer, ks.color, 0),
        (Rel.ON_LEVEL, ks.wall, ks.level, 0),
        (Rel.IN_COLLECTION, ks.wall, ks.layer, 0),
        (Rel.IN_MODEL, ks.wall, ks.model, 0),
        (Rel.IN_ROOM, ks.wall, ks.host, 0),
        (Rel.IN_SYSTEM, ks.wall, ks.system, 0),
        (Rel.IN_GROUP, ks.wall, ks.group, 0),
        (Rel.IN_ASSEMBLY, ks.host, ks.wall, 0),
        (Rel.HOSTED_ON, ks.host, ks.wall, 0),
        (Rel.BOUNDS, ks.wall, ks.host, 0),
        (Rel.CONNECTS_TO, ks.wall, ks.host, ks.system),
    }
    assert {(int(r), s, d, o) for r, s, d, o in expected} <= rels
    emitted = {r for r, *_ in rels}
    live = {int(r) for r in Rel}
    assert emitted == live - {int(Rel.SOLID)}


def test_nodes(bundle):
    _, ks, q = bundle
    nodes = {
        row[0]: row
        for row in q(
            "SELECT id, kind, name, def_ref, transform, units, subtype, argb, "
            "emissive, ior, elevation, gh_topology FROM {g}.envelope.nodes.parquet')"
        )
    }
    inst = nodes[ks.instance]
    assert inst[1] == NodeKind.INSTANCE and inst[3] == ks.definition
    assert inst[4].startswith("1.0,0.0") and inst[5] == "m"
    mat = nodes[ks.material]
    assert mat[2] == "Painted Steel" and mat[7] == -1
    assert mat[8] == -16711936 and mat[9] == 1.45
    black = nodes[ks.material + 1]
    assert black[8] is None and black[9] is None
    assert nodes[ks.layer][6] == "Layer" and nodes[ks.layer][11] == "0-1"
    assert nodes[ks.system][6] == "MEP System"
    assert nodes[ks.level][10] == 3.0
    ids = sorted(nodes)
    assert ids == list(range(len(ids)))


def test_optional_files(bundle):
    _, _, q = bundle
    csv = lambda t: ",".join(repr(float(d)) for d in t)  # noqa: E731
    assert q(
        "SELECT path, value_string, value_boolean FROM {g}.eav.model.parquet') "
        "ORDER BY path"
    ) == [
        ("modelPlacement.appliedToGeometry", None, True),
        ("modelPlacement.default", "projectBasePoint", None),
        (
            "modelPlacement.options.internalOrigin.transform",
            csv(fixture_bundle.IDENTITY),
            None,
        ),
        (
            "modelPlacement.options.projectBasePoint.transform",
            csv(fixture_bundle.PLACEMENT),
            None,
        ),
        ("modelPlacement.source", "projectBasePoint", None),
        ("modelPlacement.transform", csv(fixture_bundle.PLACEMENT), None),
        ("modelPlacement.units", "m", None),
        ("projectInformation.name", "Fixture", None),
    ]
    assert q(
        "SELECT set_name, field_name, field_bucket_id, unit "
        "FROM {g}.eav.property_set_definitions.parquet')"
    ) == [
        ("Pset_Wall", "Width", "bucket-w", "mm"),
        ("Pset_Wall", "LoadBearing", "bucket-lb", None),
    ]
    assert q(
        "SELECT name, fov, units, is_ortho FROM {g}.envelope.camera_views.parquet')"
    ) == [("Front", 45.0, "m", False)]
    assert q("SELECT ord, source, ref FROM {g}.envelope.scene_views.parquet')") == [
        (0, "rel", str(int(Rel.ON_LEVEL)))
    ]


def test_optional_files_absent_when_unused(tmp_path):
    out = str(tmp_path)
    with ObjectsArtifactPipeline(out, BASE, Producer("t", "1")) as p:
        p.intern_object("a")
    names = set(os.listdir(out))
    assert f"{BASE}.envelope.meta.parquet" in names
    assert (
        not {
            f"{BASE}.eav.model.parquet",
            f"{BASE}.eav.property_set_definitions.parquet",
            f"{BASE}.envelope.camera_views.parquet",
            f"{BASE}.envelope.scene_views.parquet",
        }
        & names
    )


def test_model_property_coalesces_one_typed_column(tmp_path):
    out = str(tmp_path)
    with ObjectsArtifactPipeline(out, BASE, Producer("t", "1")) as p:
        p.add_model_property("flag", True)
        p.add_model_property("count", 3)
        p.add_model_property("ratio", 0.5, "m")
        p.add_model_property("label", "x")
        p.add_model_property("skipped", None)
        p.add_model_property("nan", float("nan"))
    rows = duckdb.sql(
        f"SELECT * FROM read_parquet('{out}/{BASE}.eav.model.parquet') ORDER BY path"
    ).fetchall()
    assert rows == [
        ("count", None, 3.0, None, None),
        ("flag", None, None, True, None),
        ("label", "x", None, None, None),
        ("ratio", None, 0.5, None, "m"),
    ]


def _model_strings(out: str) -> dict[str, str]:
    return dict(
        duckdb.sql(
            f"SELECT path, value_string "
            f"FROM read_parquet('{out}/{BASE}.eav.model.parquet')"
        ).fetchall()
    )


def test_model_placement_rules(tmp_path):
    out = str(tmp_path)
    identity = fixture_bundle.IDENTITY
    with ObjectsArtifactPipeline(out, BASE, Producer("t", "1")) as p:
        with pytest.raises(ValueError):
            p.add_model_placement(
                "surveyPoint",
                identity,
                "m",
                False,
                options={"internalOrigin": identity},
            )
        with pytest.raises(ValueError):
            p.add_model_placement("internalOrigin", identity[:15], "m", False)
        p.add_model_placement(
            "internalOrigin", identity, "m", False, source="internalOriginFallback"
        )
    rows = _model_strings(out)
    assert rows["modelPlacement.default"] == "internalOrigin"
    assert rows["modelPlacement.source"] == "internalOriginFallback"
    assert "modelPlacement.options.internalOrigin.transform" not in rows


def test_model_placement_source_defaults_to_default(tmp_path):
    out = str(tmp_path)
    with ObjectsArtifactPipeline(out, BASE, Producer("t", "1")) as p:
        p.add_model_placement("drawingWcs", fixture_bundle.IDENTITY, "mm", True)
    rows = _model_strings(out)
    assert rows["modelPlacement.source"] == "drawingWcs"
