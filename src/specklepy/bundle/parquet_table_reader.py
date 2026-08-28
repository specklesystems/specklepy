"""Whole-column parquet reads for the bundle reader."""

from __future__ import annotations

import fnmatch
import os

import pyarrow.parquet as pq


class ParquetTable:
    def __init__(self, table) -> None:
        self._table = table

    @property
    def row_count(self) -> int:
        return self._table.num_rows

    @property
    def column_names(self) -> list[str]:
        return list(self._table.column_names)

    def has(self, column: str) -> bool:
        return column in self._table.column_names

    def _column(self, column: str) -> list:
        return self._table.column(column).to_pylist()

    def ints(self, column: str) -> list[int]:
        return [0 if v is None else int(v) for v in self._column(column)]

    def nullable_ints(self, column: str) -> list[int | None]:
        return [None if v is None else int(v) for v in self._column(column)]

    def doubles(self, column: str) -> list[float | None]:
        return [None if v is None else float(v) for v in self._column(column)]

    def bools(self, column: str) -> list[bool | None]:
        return self._column(column)

    def strings(self, column: str) -> list[str | None]:
        return self._column(column)

    def blobs(self, column: str) -> list[bytes | None]:
        return self._column(column)


def read_table(path: str) -> ParquetTable:
    return ParquetTable(pq.read_table(path))


def find_files(directory: str, pattern: str) -> list[str]:
    """Bundle files matching a glob on the basename, sorted; the ``{base}.`` prefix is
    whatever the producer chose."""
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if fnmatch.fnmatch(f, pattern)
    )


def find_table(directory: str, suffix: str, *, required: bool) -> ParquetTable | None:
    matches = find_files(directory, f"*{suffix}")
    if not matches:
        if required:
            raise FileNotFoundError(f"bundle has no '*{suffix}' in {directory}")
        return None
    return read_table(matches[0])
