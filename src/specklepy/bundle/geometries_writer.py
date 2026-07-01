"""Writes ``geometries.parquet`` — one row per geometry: (geometryIndex, content,
id, type).

Port of the .NET ``GeometriesParquetWriter``. ``geometryIndex`` is the dense
geometry-K the envelope's DISPLAY/DEFINES/HAS_MATERIAL edges reference (pure int, no
applicationId strings). ``id`` is the SHA256 of the blob, kept as a column for
READ-TIME shape dedup (the consumer collapses identical shapes into one GPU buffer);
we do NOT content-dedup at write time, so every per-mesh row stays addressable and
its material bindable.

Sharded: shard 0 keeps the canonical ``{base}.geometries.parquet`` name (a model that
fits in one shard is byte-for-byte unchanged); overflow shards are
``{base}.geometries.{N}.parquet`` (N=1,2,…). Consumers read the set via the glob
``{base}.geometries*.parquet``. The cap is on UNCOMPRESSED content bytes, so the
on-disk (Zstd) shard is always smaller than the cap — this contract is shared verbatim
with the native nwextract ``GeomSharder`` (C++).
"""

from __future__ import annotations

import glob
import hashlib
import os

import pyarrow as pa
import pyarrow.parquet as pq

from specklepy.bundle.parquet_table_writer import schema_of
from specklepy.bundle.spec import BY_TABLE

# Flush (write a row group + free the buffer) once buffered blob bytes reach this
# budget.
_DEFAULT_ROWGROUP_MB = 64
_MAX_ROWS_PER_GROUP = 200_000  # safety cap for tiny-blob models
# Roll to a new shard once the current shard's uncompressed content bytes would
# exceed this.
_DEFAULT_SHARD_MB = 1536  # 1.5 GiB uncompressed content per shard

_SGEO_HEADER_SIZE = 16
_SGEO_MAGIC = b"SGEO"

# SGEO primitive_type byte (header offset 0x05) -> geometries.type label.
_PRIMITIVE_TYPE_NAME = {
    0: "mesh",
    1: "line",
    2: "polyline",
    3: "polycurve",
    4: "curve",
    5: "arc",
    6: "circle",
    7: "points",
    8: "ellipse",
    9: "spiral",
    10: "box",
}


def _mb_env(name: str, fallback: int) -> int:
    raw = os.environ.get(name)
    try:
        v = int(raw) if raw is not None else 0
    except ValueError:
        v = 0
    return v if v > 0 else fallback


class GeometriesParquetWriter:
    def __init__(
        self, output_dir: str, base_name: str, shard_cap_bytes: int | None = None
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self._output_dir = output_dir
        self._base_name = base_name
        self._schema = schema_of(BY_TABLE["geometries"])
        self._flush_bytes = (
            _mb_env("SPECKLE_PARQUET_ROWGROUP_MB", _DEFAULT_ROWGROUP_MB) * 1024 * 1024
        )
        self._shard_cap_bytes = (
            shard_cap_bytes
            if shard_cap_bytes is not None
            else _mb_env("SPECKLE_GEOMETRY_SHARD_MB", _DEFAULT_SHARD_MB) * 1024 * 1024
        )

        self._seen: set[int] = set()
        self._geometry_paths: list[str] = []
        self._shard_index = 0
        self._shard_bytes = (
            0  # uncompressed content bytes assigned to the current shard
        )
        self._completed = False

        # in-flight row-group buffers (parallel lists, one entry per row).
        self._indices: list[int] = []
        self._contents: list[bytes] = []
        self._ids: list[str] = []
        self._types: list[str] = []
        self._buffered_bytes = 0

        self.geometries_path = self._shard_path(0)
        # a previous run may have produced MORE shards than this one will — clear the
        # whole set.
        self._delete_stale_shards()
        self._open_shard(0)

    @property
    def geometry_paths(self) -> list[str]:
        """Every geometry shard file written, in order (shard 0 =
        ``geometries_path``)."""
        return list(self._geometry_paths)

    def add_geometry(self, geometry_index: int, sgeo: bytes) -> None:
        """Add one SGEO geometry buffer under its dense ``geometry_index``.

        ``id`` is the SHA256 of the blob; ``type`` is read from the SGEO header.
        """
        if len(sgeo) < _SGEO_HEADER_SIZE or sgeo[0:4] != _SGEO_MAGIC:
            raise ValueError("Buffer is not a valid SGEO blob.")
        self._add_row(
            geometry_index, sgeo, _PRIMITIVE_TYPE_NAME.get(sgeo[5], "unknown")
        )

    def add_raw_geometry(
        self, geometry_index: int, content: bytes, type_label: str
    ) -> None:
        """Add one RAW (non-SGEO) blob verbatim with an explicit ``type`` label
        (e.g. "3dm")."""
        self._add_row(geometry_index, content, type_label)

    def complete(self) -> None:
        if self._completed:
            return
        self._completed = True
        self._flush_row_group()
        self._finalize_current_shard()

    def __enter__(self) -> GeometriesParquetWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.complete()

    # ── internals ──────────────────────────────────────────────────────────

    def _shard_path(self, shard_index: int) -> str:
        name = (
            f"{self._base_name}.geometries.parquet"
            if shard_index == 0
            else f"{self._base_name}.geometries.{shard_index}.parquet"
        )
        return os.path.join(self._output_dir, name)

    def _open_shard(self, shard_index: int) -> None:
        path = self._shard_path(shard_index)
        self._writer = pq.ParquetWriter(path, self._schema, compression="zstd")
        self._shard_bytes = 0
        self._geometry_paths.append(path)

    def _finalize_current_shard(self) -> None:
        self._writer.close()

    def _roll_shard(self) -> None:
        self._flush_row_group()
        self._finalize_current_shard()
        self._shard_index += 1
        self._open_shard(self._shard_index)

    def _delete_stale_shards(self) -> None:
        for stale in [
            self._shard_path(0),
            *glob.glob(
                self._shard_path(0).replace(
                    ".geometries.parquet", ".geometries.*.parquet"
                )
            ),
        ]:
            if os.path.exists(stale):
                os.remove(stale)

    def _add_row(self, geometry_index: int, content: bytes, type_label: str) -> None:
        if self._completed:
            raise RuntimeError("Writer already completed.")
        if geometry_index in self._seen:
            return
        self._seen.add(geometry_index)

        # Roll before this blob would push the current shard past the cap. Guard on
        # _shard_bytes > 0 so a single over-cap blob still lands in its own shard.
        if (
            self._shard_bytes > 0
            and self._shard_bytes + len(content) > self._shard_cap_bytes
        ):
            self._roll_shard()

        self._indices.append(geometry_index)
        self._contents.append(content)
        self._ids.append(hashlib.sha256(content).hexdigest())
        self._types.append(type_label)
        self._buffered_bytes += len(content)
        self._shard_bytes += len(content)

        if (
            self._buffered_bytes >= self._flush_bytes
            or len(self._indices) >= _MAX_ROWS_PER_GROUP
        ):
            self._flush_row_group()

    def _flush_row_group(self) -> None:
        if not self._indices:
            return
        table = pa.Table.from_arrays(
            [
                pa.array(self._indices, type=pa.int32()),
                pa.array(self._contents, type=pa.binary()),
                pa.array(self._ids, type=pa.string()),
                pa.array(self._types, type=pa.string()),
            ],
            schema=self._schema,
        )
        self._writer.write_table(table, row_group_size=len(table))
        self._indices.clear()
        self._contents.clear()
        self._ids.clear()
        self._types.clear()
        self._buffered_bytes = 0
