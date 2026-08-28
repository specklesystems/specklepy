"""Optional ``{base}.eav.property_set_definitions.parquet`` — property-set schemas.

One row per field, in authored field order. Values stay in ``eav`` under
``properties.Property Sets.{set}.{field}`` with
``internal_definition_name = field_bucket_id``.
"""

from __future__ import annotations

import os

from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import BY_TABLE, PROPERTY_SET_DEFINITIONS


class PropertySetDefinitionsWriter:
    def __init__(self, output_dir: str, base_name: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self._rows = ParquetTableWriter(
            os.path.join(
                output_dir, f"{base_name}.eav.property_set_definitions.parquet"
            ),
            schema_of(BY_TABLE["property_set_definitions"]),
            table="property_set_definitions",
            column_count=PROPERTY_SET_DEFINITIONS.COLUMN_COUNT,
        )

    def add_row(
        self,
        set_name: str,
        set_key: str,
        set_description: str | None,
        field_name: str,
        field_bucket_id: str | None,
        data_type: str | None,
        default_string: str | None,
        default_double: float | None,
        default_boolean: bool | None,
        unit: str | None,
        description: str | None,
        applies_to: str | None,
    ) -> None:
        defaults = sum(
            v is not None for v in (default_string, default_double, default_boolean)
        )
        if defaults > 1:
            raise ValueError(
                f"property-set field '{set_name}.{field_name}': "
                "at most one default may be set"
            )
        self._rows.add_row_at(
            {
                PROPERTY_SET_DEFINITIONS.SET_NAME: set_name,
                PROPERTY_SET_DEFINITIONS.SET_KEY: set_key,
                PROPERTY_SET_DEFINITIONS.SET_DESCRIPTION: set_description,
                PROPERTY_SET_DEFINITIONS.FIELD_NAME: field_name,
                PROPERTY_SET_DEFINITIONS.FIELD_BUCKET_ID: field_bucket_id,
                PROPERTY_SET_DEFINITIONS.DATA_TYPE: data_type,
                PROPERTY_SET_DEFINITIONS.DEFAULT_STRING: default_string,
                PROPERTY_SET_DEFINITIONS.DEFAULT_DOUBLE: default_double,
                PROPERTY_SET_DEFINITIONS.DEFAULT_BOOLEAN: default_boolean,
                PROPERTY_SET_DEFINITIONS.UNIT: unit,
                PROPERTY_SET_DEFINITIONS.DESCRIPTION: description,
                PROPERTY_SET_DEFINITIONS.APPLIES_TO: applies_to,
            }
        )

    def complete(self) -> None:
        self._rows.complete()
