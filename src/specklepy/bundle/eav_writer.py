"""Compact, interned EAV writer — direct Zstd parquet, one file per table.

Port of the .NET ``EavWriter``. Passive columnar files, no WAL/checkpoint/index::

  {base}.eav.objects.parquet(object_index, application_id)      -- the K dictionary
  {base}.eav.paths.parquet(path_index, path)                    -- shared path vocabulary
  {base}.eav.eav.parquet(object_index, path_index, value_*)     -- INSTANCE-scoped rows
  {base}.eav.types.parquet(type_index, type_key)                -- type dictionary
  {base}.eav.type_eav.parquet(type_index, path_index, value_*)  -- TYPE-scoped, once per type
  {base}.eav.object_type.parquet(object_index, type_index)      -- the weak ref

No manifest is written: consumers build their own ``read_parquet`` views (the read recipe
lives in notes/topology-envelope-SOT.md §4/§6). Interning (applicationId/path/type_key ->
dense int) and type dedup are unchanged. Not thread-safe: calls are sequential.
"""

from __future__ import annotations

import os
from typing import Callable, Iterable

from specklepy.bundle.eav_extraction import EavRow
from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import BY_TABLE


def _value_boolean(row: EavRow) -> bool | None:
    if row.type != "boolean":
        return None
    if isinstance(row.value_text, bool):
        return row.value_text
    lowered = (row.value_text or "").strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


class EavWriter:
    def __init__(self, output_dir: str, base_name: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.base_name = base_name

        self._objects = ParquetTableWriter(
            self._p("objects.parquet"), schema_of(BY_TABLE["objects"])
        )
        self._paths = ParquetTableWriter(
            self._p("paths.parquet"), schema_of(BY_TABLE["paths"])
        )
        self._eav = ParquetTableWriter(
            self._p("eav.parquet"), schema_of(BY_TABLE["eav"])
        )
        self._types = ParquetTableWriter(
            self._p("types.parquet"), schema_of(BY_TABLE["types"])
        )
        self._type_eav = ParquetTableWriter(
            self._p("type_eav.parquet"), schema_of(BY_TABLE["type_eav"])
        )
        self._object_type = ParquetTableWriter(
            self._p("object_type.parquet"), schema_of(BY_TABLE["object_type"])
        )

        # interning: applicationId / path / type_key -> dense sequential int (first-seen order).
        self._object_index: dict[str, int] = {}
        self._path_index: dict[str, int] = {}
        self._type_index: dict[str, int] = {}
        self._completed = False

    @property
    def eav_db_path(self) -> str:
        """The directory holding this artefact's parquet tables (no single entry file)."""
        return self.output_dir

    def get_or_add_object(self, application_id: str) -> int:
        """Intern ``application_id`` to its dense object_index, writing the dict row on first sight.

        Public so the envelope path resolves the SAME K for an object's edges.
        """
        idx = self._object_index.get(application_id)
        if idx is not None:
            return idx
        idx = len(self._object_index)
        self._object_index[application_id] = idx
        self._objects.add_row(idx, application_id)
        return idx

    def add_rows(self, application_id: str, rows: Iterable[EavRow]) -> None:
        """Append the flattened rows for one object, keyed by its ``application_id``."""
        self._ensure_not_completed()
        object_index = self.get_or_add_object(application_id)
        for row in rows:
            self._eav.add_row(
                object_index,
                self._get_or_add_path(row.path),
                row.value_text,
                row.value_num,
                _value_boolean(row),
                row.units,
                row.internal_definition_name,
            )

    def add_type(
        self,
        application_id: str,
        type_key: str,
        type_rows_factory: Callable[[], Iterable[EavRow]],
    ) -> None:
        """Link an object to its type via ``object_type`` and write the type's params ONCE.

        ``type_rows_factory`` is invoked only on the type's first sight (dedup).
        """
        self._ensure_not_completed()
        type_index, is_new = self._get_or_add_type(type_key)
        if is_new:
            for row in type_rows_factory():
                self._type_eav.add_row(
                    type_index,
                    self._get_or_add_path(row.path),
                    row.value_text,
                    row.value_num,
                    _value_boolean(row),
                    row.units,
                    row.internal_definition_name,
                )
        self._object_type.add_row(self.get_or_add_object(application_id), type_index)

    def complete(self) -> None:
        if self._completed:
            return
        self._completed = True
        for w in (
            self._objects,
            self._paths,
            self._eav,
            self._types,
            self._type_eav,
            self._object_type,
        ):
            w.complete()

    def _get_or_add_path(self, path: str) -> int:
        idx = self._path_index.get(path)
        if idx is not None:
            return idx
        idx = len(self._path_index)
        self._path_index[path] = idx
        self._paths.add_row(idx, path)
        return idx

    def _get_or_add_type(self, type_key: str) -> tuple[int, bool]:
        idx = self._type_index.get(type_key)
        if idx is not None:
            return idx, False
        idx = len(self._type_index)
        self._type_index[type_key] = idx
        self._types.add_row(idx, type_key)
        return idx, True

    def _p(self, suffix: str) -> str:
        return os.path.join(self.output_dir, f"{self.base_name}.eav.{suffix}")

    def _ensure_not_completed(self) -> None:
        if self._completed:
            raise RuntimeError("Writer already completed.")
