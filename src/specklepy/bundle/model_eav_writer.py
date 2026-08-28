"""Optional ``{base}.eav.model.parquet`` — document-scoped rows without an object."""

from __future__ import annotations

import os

from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import BY_TABLE, MODEL


class ModelEavWriter:
    def __init__(self, output_dir: str, base_name: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self._rows = ParquetTableWriter(
            os.path.join(output_dir, f"{base_name}.eav.model.parquet"),
            schema_of(BY_TABLE["model"]),
            table="model",
            column_count=MODEL.COLUMN_COUNT,
        )

    def add_row(
        self,
        path: str,
        value_string: str | None,
        value_double: float | None,
        value_boolean: bool | None,
        unit: str | None,
    ) -> None:
        set_count = sum(
            v is not None for v in (value_string, value_double, value_boolean)
        )
        if set_count != 1:
            raise ValueError(
                f"model row '{path}': exactly one value column must be set, "
                f"got {set_count}"
            )
        self._rows.add_row_at(
            {
                MODEL.PATH: path,
                MODEL.VALUE_STRING: value_string,
                MODEL.VALUE_DOUBLE: value_double,
                MODEL.VALUE_BOOLEAN: value_boolean,
                MODEL.UNIT: unit,
            }
        )

    def complete(self) -> None:
        self._rows.complete()
