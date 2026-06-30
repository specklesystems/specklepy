"""Core bundle writer tests: write parquet, read it back with DuckDB, check spec conformance."""

from __future__ import annotations

import hashlib
import os

import duckdb
import pytest

from specklepy.bundle.eav_extraction import EavRow
from specklepy.bundle.eav_writer import EavWriter
from specklepy.bundle.envelope_writer import EnvelopeWriter
from specklepy.bundle.geometries_writer import GeometriesParquetWriter
from specklepy.bundle.spec import SCHEMA_VERSION, NodeKind, Rel

BASE = "test"


def _q(con, sql):
    return con.execute(sql).fetchall()


def test_envelope_writer_roundtrip_and_catalog(tmp_path):
    out = str(tmp_path)
    w = EnvelopeWriter(out, BASE)
    # one container (subtype Model) + one object→container edge
    w.add_node(
        0,
        NodeKind.CONTAINER,
        "Model A",
        None,
        None,
        None,
        "Model",
        None,
        None,
        None,
        None,
        None,
    )
    w.add_node(
        1, NodeKind.LEVEL, "L1", None, None, None, None, None, None, None, None, 3.5
    )
    w.add_relation(Rel.IN_MODEL, 0, 0, 0)
    w.add_relation(Rel.ON_LEVEL, 0, 1, 0)
    w.complete()

    con = duckdb.connect()

    # meta: schema version from the spec
    (ver,) = _q(
        con,
        f"SELECT schema_version FROM read_parquet('{out}/{BASE}.envelope.meta.parquet')",
    )[0:1]
    assert ver[0] == SCHEMA_VERSION == 5

    # rel_types catalog: 15 live+reserved (retired absent)
    (n_rel,) = _q(
        con,
        f"SELECT count(*) FROM read_parquet('{out}/{BASE}.envelope.rel_types.parquet')",
    )[0]
    assert n_rel == 15
    # retired ids never present
    retired = _q(
        con,
        f"SELECT count(*) FROM read_parquet('{out}/{BASE}.envelope.rel_types.parquet') "
        "WHERE rel IN (13,15,16,17,18,19,20,22)",
    )[0][0]
    assert retired == 0

    # node_kinds catalog: 6 live (COLLECTION retired/folded)
    n_kind = _q(
        con,
        f"SELECT count(*) FROM read_parquet('{out}/{BASE}.envelope.node_kinds.parquet')",
    )[0][0]
    assert n_kind == 6

    # nodes + relations content
    nodes = _q(
        con,
        f"SELECT id, kind, name, subtype, elevation FROM read_parquet('{out}/{BASE}.envelope.nodes.parquet') ORDER BY id",
    )
    assert nodes[0][1] == int(NodeKind.CONTAINER) and nodes[0][3] == "Model"
    assert nodes[1][1] == int(NodeKind.LEVEL) and nodes[1][4] == 3.5
    rels = _q(
        con,
        f"SELECT rel, src, dst FROM read_parquet('{out}/{BASE}.envelope.relations.parquet') ORDER BY rel",
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
        f"SELECT object_index, application_id FROM read_parquet('{out}/{BASE}.eav.objects.parquet')",
    )
    assert objs == [(0, "guid-1")]

    # join eav -> paths and coalesce values
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
    """Minimal valid-enough SGEO blob: 16-byte header (magic/version/type) + body."""
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
    w.add_geometry(7, blob)  # dedup by geometryIndex -> one row
    w.complete()

    con = duckdb.connect()
    rows = _q(
        con,
        f"SELECT geometryIndex, id, type FROM read_parquet('{out}/{BASE}.geometries.parquet')",
    )
    assert len(rows) == 1
    assert rows[0][0] == 7
    assert rows[0][1] == hashlib.sha256(blob).hexdigest()
    assert rows[0][2] == "mesh"


def test_geometries_writer_rejects_non_sgeo(tmp_path):
    w = GeometriesParquetWriter(str(tmp_path), BASE)
    with pytest.raises(ValueError):
        w.add_geometry(0, b"NOPE")
    w.complete()


def test_geometries_sharding(tmp_path):
    out = str(tmp_path)
    # tiny cap forces a roll: each blob ~24 bytes, cap 30 -> shard 0 gets one, shard 1 next.
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
