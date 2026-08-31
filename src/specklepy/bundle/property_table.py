"""Columnar eav storage: parallel arrays sorted by key, read through dict-like views."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from specklepy.bundle.parquet_table_reader import ParquetTable


def coalesce(
    boolean: bool | None, double: float | None, string: str | None
) -> object | None:
    if boolean is not None:
        return boolean
    if double is not None:
        return double
    return string


class PropertyTable:
    def __init__(
        self,
        keys: list[int],
        path_ids: list[int],
        strings: list[str | None],
        doubles: list[float | None],
        bools: list[bool | None],
        path_by_id: list[str],
        id_by_path: dict[str, int],
        ranges: dict[int, tuple[int, int]],
    ) -> None:
        self._key = keys
        self._path_id = path_ids
        self._str = strings
        self._dbl = doubles
        self._bool = bools
        self._path_by_id = path_by_id
        self._id_by_path = id_by_path
        self._range = ranges

    @classmethod
    def empty(cls) -> PropertyTable:
        return cls([], [], [], [], [], [], {}, {})

    @classmethod
    def load(
        cls, eav: ParquetTable | None, paths: ParquetTable, key_column: str
    ) -> PropertyTable:
        p_idx = paths.ints("path_index")
        p_str = paths.strings("path")
        path_by_id = [""] * (max(p_idx, default=-1) + 1)
        id_by_path: dict[str, int] = {}
        for idx, path in zip(p_idx, p_str, strict=True):
            path = path or ""
            path_by_id[idx] = path
            if path:
                id_by_path[path] = idx

        if eav is None or not eav.has(key_column):
            return cls([], [], [], [], [], path_by_id, id_by_path, {})

        key = eav.ints(key_column)
        path_id = eav.ints("path_index")
        strings = eav.strings("value_string")
        doubles = eav.doubles("value_double")
        bools = eav.bools("value_boolean")

        keep = [
            i
            for i in range(len(key))
            if (
                bools[i] is not None or doubles[i] is not None or strings[i] is not None
            )
            and 0 <= path_id[i] < len(path_by_id)
            and path_by_id[path_id[i]]
        ]
        keep.sort(key=lambda i: key[i])

        ranges: dict[int, tuple[int, int]] = {}
        for row, i in enumerate(keep):
            start, count = ranges.get(key[i], (row, 0))
            ranges[key[i]] = (start, count + 1)

        return cls(
            [key[i] for i in keep],
            [path_id[i] for i in keep],
            [strings[i] for i in keep],
            [doubles[i] for i in keep],
            [bools[i] for i in keep],
            path_by_id,
            id_by_path,
            ranges,
        )

    @property
    def row_count(self) -> int:
        return len(self._key)

    @property
    def paths(self) -> list[str]:
        return [p for p in self._path_by_id if p]

    @property
    def keys(self) -> list[int]:
        return list(self._range)

    def contains(self, key: int) -> bool:
        return key in self._range

    def path_id(self, path: str) -> int:
        return self._id_by_path.get(path, -1)

    def view(self, key: int) -> PropertyView:
        start, count = self._range.get(key, (0, 0))
        return PropertyView(self, start, count, None)

    def under(self, key: int, prefix: str) -> PropertyView:
        start, count = self._range.get(key, (0, 0))
        return PropertyView(self, start, count, prefix + ".")

    def try_get(self, key: int, path: str) -> tuple[bool, object | None]:
        row = self._find_row(key, path)
        return (row >= 0, self._value_at(row) if row >= 0 else None)

    def get_string(self, key: int, path: str) -> str | None:
        row = self._find_row(key, path)
        return self._str[row] if row >= 0 else None

    def get_double(self, key: int, path: str) -> float | None:
        row = self._find_row(key, path)
        return self._dbl[row] if row >= 0 else None

    def get_bool(self, key: int, path: str) -> bool | None:
        row = self._find_row(key, path)
        return self._bool[row] if row >= 0 else None

    def keys_with(self, path: str) -> Iterator[int]:
        pid = self.path_id(path)
        if pid < 0:
            return
        last: int | None = None
        for row, p in enumerate(self._path_id):
            if p == pid and self._key[row] != last:
                last = self._key[row]
                yield last

    def values_of(self, path: str) -> Iterator[tuple[int, object | None]]:
        pid = self.path_id(path)
        if pid < 0:
            return
        for row, p in enumerate(self._path_id):
            if p == pid:
                yield self._key[row], self._value_at(row)

    def _path_at(self, row: int) -> str:
        return self._path_by_id[self._path_id[row]]

    def _value_at(self, row: int) -> object | None:
        return coalesce(self._bool[row], self._dbl[row], self._str[row])

    def _find_row(self, key: int, path: str) -> int:
        span = self._range.get(key)
        pid = self._id_by_path.get(path)
        if span is None or pid is None:
            return -1
        return self._find_row_in(span[0], span[1], pid)

    def _find_row_in(self, start: int, count: int, pid: int) -> int:
        for row in range(start, start + count):
            if self._path_id[row] == pid:
                return row
        return -1


class PropertyView(Mapping[str, Any]):
    """One key's rows, optionally restricted to a dotted prefix that is stripped from
    the exposed keys."""

    def __init__(
        self, table: PropertyTable, start: int, count: int, prefix: str | None
    ) -> None:
        self._table = table
        self._start = start
        self._count = count
        self._prefix = prefix

    def under(self, prefix: str) -> PropertyView:
        if not prefix:
            return self
        return PropertyView(
            self._table, self._start, self._count, (self._prefix or "") + prefix + "."
        )

    @property
    def prefix(self) -> str | None:
        return self._prefix[:-1] if self._prefix else None

    def _row(self, key: str) -> int:
        path = key if self._prefix is None else self._prefix + key
        return self._table._find_row_in(
            self._start, self._count, self._table.path_id(path)
        )

    def _rows(self) -> Iterator[tuple[int, str]]:
        for row in range(self._start, self._start + self._count):
            path = self._table._path_at(row)
            if self._prefix is None:
                yield row, path
            elif path.startswith(self._prefix):
                yield row, path[len(self._prefix) :]

    def __getitem__(self, key: str) -> object | None:
        row = self._row(key)
        if row < 0:
            raise KeyError(key)
        return self._table._value_at(row)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self._row(key) >= 0

    def __iter__(self) -> Iterator[str]:
        return (key for _, key in self._rows())

    def __len__(self) -> int:
        return sum(1 for _ in self._rows())

    def get_string(self, key: str) -> str | None:
        row = self._row(key)
        return self._table._str[row] if row >= 0 else None

    def get_double(self, key: str) -> float | None:
        row = self._row(key)
        return self._table._dbl[row] if row >= 0 else None

    def get_bool(self, key: str) -> bool | None:
        row = self._row(key)
        return self._table._bool[row] if row >= 0 else None

    def to_nested(self) -> dict[str, Any]:
        root: dict[str, Any] = {}
        for key, value in self.items():
            parts = key.split(".")
            cursor = root
            for part in parts[:-1]:
                child = cursor.get(part)
                if not isinstance(child, dict):
                    child = {}
                    cursor[part] = child
                cursor = child
            cursor[parts[-1]] = value
        return root

    def __repr__(self) -> str:
        return f"PropertyView({dict(self)!r})"
