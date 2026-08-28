"""Core bundle writer tests: write parquet, read it back with DuckDB, check spec
conformance."""

from __future__ import annotations

import hashlib
import os

import duckdb
import pyarrow as pa
import pytest

from specklepy.bundle.eav_extraction import EavRow
from specklepy.bundle.eav_writer import EavWriter
from specklepy.bundle.envelope_writer import EnvelopeWriter, Producer
from specklepy.bundle.geometries_writer import GeometriesParquetWriter
from specklepy.bundle.model_eav_writer import ModelEavWriter
from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.property_set_definitions_writer import (
    PropertySetDefinitionsWriter,
)
from specklepy.bundle.spec import (
    BY_TABLE,
    NODE_KINDS,
    NODES,
    REL_TYPES,
    SCHEMA_VERSION,
    NodeKind,
    Rel,
)

BASE = "test"
PRODUCER = Producer("test", "0", migrated_from_schema_version=3)


def _q(con, sql):
    return con.execute(sql).fetchall()


def test_envelope_writer_roundtrip_and_catalog(tmp_path):
    out = str(tmp_path)
    w = EnvelopeWriter(out, BASE, PRODUCER)
    w.add_node(0, NodeKind.CONTAINER, name="Model A", subtype="Model")
    w.add_node(1, NodeKind.LEVEL, name="L1", elevation=3.5)
    w.add_node(
        2,
        NodeKind.MATERIAL,
        name="Glass",
        argb=-1,
        opacity=0.4,
        metalness=0.0,
        roughness=0.1,
        emissive=-16711936,
        ior=1.52,
    )
    w.add_relation(Rel.IN_MODEL, 0, 0, 0)
    w.add_relation(Rel.ON_LEVEL, 0, 1, 0)
    w.complete()

    con = duckdb.connect()

    meta = _q(con, f"SELECT * FROM read_parquet('{out}/{BASE}.envelope.meta.parquet')")
    assert meta == [(SCHEMA_VERSION, "test", "0", "specklepy", PRODUCER.sdk_version, 3)]

    expected_live = sum(1 for r in REL_TYPES if r.status != "retired")
    retired_ids = [r.id for r in REL_TYPES if r.status == "retired"]
    assert expected_live > 0 and retired_ids
    (n_rel,) = _q(
        con,
        f"SELECT count(*) FROM read_parquet('{out}/{BASE}.envelope.rel_types.parquet')",
    )[0]
    assert n_rel == expected_live
    retired = _q(
        con,
        f"SELECT count(*) FROM read_parquet('{out}/{BASE}.envelope.rel_types.parquet') "
        f"WHERE rel IN ({','.join(str(i) for i in retired_ids)})",
    )[0][0]
    assert retired == 0

    n_kind = _q(
        con,
        f"SELECT count(*) FROM "
        f"read_parquet('{out}/{BASE}.envelope.node_kinds.parquet')",
    )[0][0]
    assert n_kind == sum(1 for k in NODE_KINDS if k.status != "retired")

    described = _q(
        con,
        f"DESCRIBE SELECT * FROM read_parquet('{out}/{BASE}.envelope.nodes.parquet')",
    )
    assert [d[0] for d in described] == [c.name for c in BY_TABLE["nodes"]]

    nodes = _q(
        con,
        f"SELECT id, kind, name, subtype, elevation, emissive, ior "
        f"FROM read_parquet('{out}/{BASE}.envelope.nodes.parquet') ORDER BY id",
    )
    assert nodes[0][1] == int(NodeKind.CONTAINER) and nodes[0][3] == "Model"
    assert nodes[1][1] == int(NodeKind.LEVEL) and nodes[1][4] == 3.5
    assert nodes[0][5] is None and nodes[0][6] is None
    assert nodes[2][1] == int(NodeKind.MATERIAL)
    assert nodes[2][4] is None
    assert nodes[2][5] == -16711936
    assert nodes[2][6] == 1.52
    rels = _q(
        con,
        f"SELECT rel, src, dst FROM "
        f"read_parquet('{out}/{BASE}.envelope.relations.parquet') ORDER BY rel",
    )
    assert (int(Rel.ON_LEVEL), 0, 1) in rels and (int(Rel.IN_MODEL), 0, 0) in rels


def test_eav_writer_roundtrip(tmp_path):
    out = str(tmp_path)
    w = EavWriter(out, BASE)
    rows = [
        EavRow("guid-1", "properties.Pset.Width", "100", 100.0, "number", "mm", None),
        EavRow("guid-1", "name", "Wall", None, "string", None, None),
        EavRow(
            "guid-1", "properties.Pset.LoadBearing", "true", None, "boolean", None, None
        ),
    ]
    w.add_rows("guid-1", rows)
    w.complete()

    con = duckdb.connect()
    objs = _q(
        con,
        f"SELECT object_index, application_id "
        f"FROM read_parquet('{out}/{BASE}.eav.objects.parquet')",
    )
    assert objs == [(0, "guid-1")]

    res = _q(
        con,
        f"""
        SELECT p.path, e.value_string, e.value_double, e.value_boolean, e.unit
        FROM read_parquet('{out}/{BASE}.eav.eav.parquet') e
        JOIN read_parquet('{out}/{BASE}.eav.paths.parquet') p USING (path_index)
        ORDER BY p.path
        """,
    )
    by_path = {r[0]: r for r in res}
    assert by_path["properties.Pset.Width"][2] == 100.0
    assert by_path["properties.Pset.Width"][4] == "mm"
    assert by_path["name"][1] == "Wall"
    assert by_path["properties.Pset.LoadBearing"][3] is True


def _fake_sgeo(primitive_type: int = 0, body: bytes = b"\x00" * 8) -> bytes:
    header = bytearray(16)
    header[0:4] = b"SGEO"
    header[4] = 1
    header[5] = primitive_type
    return bytes(header) + body


def test_geometries_writer_id_is_sha256_and_type_from_header(tmp_path):
    out = str(tmp_path)
    blob = _fake_sgeo(primitive_type=0, body=b"\x01\x02\x03\x04\x05\x06\x07\x08")
    w = GeometriesParquetWriter(out, BASE)
    w.add_geometry(7, blob)
    w.add_geometry(7, blob)
    w.add_geometry(8, _fake_sgeo(primitive_type=11))
    w.add_geometry(9, _fake_sgeo(primitive_type=12))
    w.complete()

    con = duckdb.connect()
    rows = _q(
        con,
        f"SELECT geometryIndex, id, type "
        f"FROM read_parquet('{out}/{BASE}.geometries.parquet') ORDER BY geometryIndex",
    )
    assert len(rows) == 3
    assert rows[0] == (7, hashlib.sha256(blob).hexdigest(), "mesh")
    assert rows[1][2] == "region" and rows[2][2] == "text"


def test_geometries_writer_rejects_non_sgeo(tmp_path):
    w = GeometriesParquetWriter(str(tmp_path), BASE)
    with pytest.raises(ValueError):
        w.add_geometry(0, b"NOPE")
    w.complete()


def test_add_row_arity_mismatch_names_the_table(tmp_path):
    w = ParquetTableWriter(
        str(tmp_path / "nodes.parquet"), schema_of(BY_TABLE["nodes"]), table="nodes"
    )
    with pytest.raises(ValueError, match=r"table 'nodes'.*12 values.*15 columns"):
        w.add_row(0, 1, None, None, None, None, None, None, None, None, None, None)
    w.complete()


def test_add_row_at_requires_every_column(tmp_path):
    w = ParquetTableWriter(
        str(tmp_path / "nodes.parquet"), schema_of(BY_TABLE["nodes"]), table="nodes"
    )
    with pytest.raises(ValueError, match=r"table 'nodes'.*indexed row"):
        w.add_row_at({NODES.ID: 0, NODES.KIND: 1})
    w.complete()


def test_column_count_guard_catches_schema_drift(tmp_path):
    with pytest.raises(ValueError, match=r"table 'nodes'.*declare 15"):
        ParquetTableWriter(
            str(tmp_path / "nodes.parquet"),
            pa.schema([pa.field("id", pa.int32())]),
            table="nodes",
            column_count=NODES.COLUMN_COUNT,
        )


def test_model_eav_writer_requires_exactly_one_value(tmp_path):
    w = ModelEavWriter(str(tmp_path), BASE)
    with pytest.raises(ValueError):
        w.add_row("p", "s", 1.0, None, None)
    with pytest.raises(ValueError):
        w.add_row("p", None, None, None, None)
    w.add_row("p", None, None, False, None)
    w.complete()
    rows = duckdb.sql(
        f"SELECT * FROM read_parquet('{tmp_path}/{BASE}.eav.model.parquet')"
    ).fetchall()
    assert rows == [("p", None, None, False, None)]


def test_property_set_definitions_writer_allows_at_most_one_default(tmp_path):
    w = PropertySetDefinitionsWriter(str(tmp_path), BASE)
    with pytest.raises(ValueError):
        w.add_row("S", "k", None, "f", None, None, "a", 1.0, None, None, None, None)
    w.add_row("S", "k", None, "f", "b", "double", None, 1.0, None, "mm", None, None)
    w.complete()
    rows = duckdb.sql(
        f"SELECT set_name, field_name, default_double, unit FROM "
        f"read_parquet('{tmp_path}/{BASE}.eav.property_set_definitions.parquet')"
    ).fetchall()
    assert rows == [("S", "f", 1.0, "mm")]


def test_geometries_sharding(tmp_path):
    out = str(tmp_path)
    w = GeometriesParquetWriter(out, BASE, shard_cap_bytes=30)
    for i in range(3):
        w.add_geometry(i, _fake_sgeo(body=bytes([i]) * 8))
    w.complete()

    assert os.path.exists(f"{out}/{BASE}.geometries.parquet")
    assert os.path.exists(f"{out}/{BASE}.geometries.1.parquet")
    con = duckdb.connect()
    total = _q(
        con, f"SELECT count(*) FROM read_parquet('{out}/{BASE}.geometries*.parquet')"
    )[0][0]
    assert total == 3
