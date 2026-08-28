"""Generic columnar Parquet table writer (Zstd), row-group-buffered.

A passive columnar file: append row groups and close — no WAL/checkpoint/transaction
manager/index. Memory is bounded by the in-flight row group (flushed on a row budget),
so it scales to arbitrary row counts at constant memory. DuckDB reads it natively
(``read_parquet('...')``). Port of the .NET ``ParquetTableWriter``.

Unlike the .NET writer there is no background scheduler: the .NET version offloads the
sync-over-async parquet IO to a worker thread only to keep it off the ODA-pinned
extraction thread. specklepy has no such constraint, so writes happen inline.

Rows are added as a positional sequence in schema-column order; nullable columns accept
``None``. Not thread-safe: calls are sequential (converter loop).
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

from specklepy.bundle.spec import ColumnSpec

DEFAULT_ROWGROUP_ROWS = 200_000

# ColumnSpec.type token (from the generated spec) -> pyarrow type. The single mapping
# point; every table schema is built from the spec descriptors, never hand-declared.
_ARROW: dict[str, pa.DataType] = {
    "int32": pa.int32(),
    "int64": pa.int64(),
    "string": pa.string(),
    "float64": pa.float64(),
    "bool": pa.bool_(),
    "binary": pa.binary(),
}


def arrow_field(col: ColumnSpec) -> pa.Field:
    """One pyarrow field from a generated column descriptor (name, type token,
    nullability)."""
    try:
        dt = _ARROW[col.type]
    except KeyError as exc:  # pragma: no cover - guards a spec/codegen mismatch
        raise NotImplementedError(
            f"unmapped arrow type token '{col.type}' for column '{col.name}'"
        ) from exc
    return pa.field(col.name, dt, nullable=col.nullable)


def schema_of(cols: Sequence[ColumnSpec]) -> pa.Schema:
    """Build a pyarrow schema from the generated spec column descriptors."""
    return pa.schema([arrow_field(c) for c in cols])


class ParquetTableWriter:
    """Buffers rows and flushes Zstd-compressed row groups to a single parquet file."""

    def __init__(
        self,
        path: str,
        schema: pa.Schema,
        flush_rows: int = DEFAULT_ROWGROUP_ROWS,
        table: str | None = None,
        column_count: int | None = None,
    ) -> None:
        self.path = path
        if column_count is not None and column_count != len(schema):
            raise ValueError(
                f"table '{table or os.path.basename(path)}': schema has {len(schema)} "
                f"columns but the generated column constants declare {column_count}"
            )
        if os.path.exists(path):
            os.remove(path)

        # spec table name for diagnostics (falls back to the file name); an arity
        # mismatch must say WHICH table drifted from the vendored spec.
        self.table = table or os.path.basename(path)
        self._schema = schema
        self._flush_rows = flush_rows
        # one buffer list per column, in schema order.
        self._cols: list[list[Any]] = [[] for _ in range(len(schema))]
        self._buffered = 0
        self._completed = False
        self._writer = pq.ParquetWriter(path, schema, compression="zstd")

    def add_row(self, *values: Any) -> None:
        """Append one row; ``values`` are in schema-column order."""
        if self._completed:
            raise RuntimeError("Writer already completed.")
        if len(values) != len(self._cols):
            # The exact failure mode of the Jul-2026 envelope incident (in the C++
            # writers): schema updated from the spec, row assembly not. Fail loudly,
            # naming the table, instead of writing a malformed/empty artefact.
            raise ValueError(
                f"table '{self.table}': row has {len(values)} values but the schema "
                f"has {len(self._cols)} columns "
                f"({', '.join(self._schema.names)}) — row assembly is out of sync "
                f"with the vendored bundle spec ({self.path})"
            )
        for col, v in zip(self._cols, values, strict=True):
            col.append(v)
        self._buffered += 1
        if self._buffered >= self._flush_rows:
            self._flush_row_group()

    def add_row_at(self, values: Mapping[int, Any]) -> None:
        """Append one row addressed by generated column index; every column required."""
        if len(values) != len(self._cols) or any(
            not 0 <= i < len(self._cols) for i in values
        ):
            raise ValueError(
                f"table '{self.table}': indexed row covers {sorted(values)} but the "
                f"schema has columns 0..{len(self._cols) - 1}"
            )
        self.add_row(*(values[i] for i in range(len(self._cols))))

    def complete(self) -> None:
        """Flush the final row group and close the file (writes the footer/metadata)."""
        if self._completed:
            return
        self._completed = True
        self._flush_row_group()
        self._writer.close()

    def __enter__(self) -> ParquetTableWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.complete()

    def _flush_row_group(self) -> None:
        if self._buffered == 0:
            return
        arrays = [
            pa.array(self._cols[i], type=self._schema.field(i).type)
            for i in range(len(self._cols))
        ]
        table = pa.Table.from_arrays(arrays, schema=self._schema)
        self._writer.write_table(table, row_group_size=len(table))
        for col in self._cols:
            col.clear()
        self._buffered = 0
