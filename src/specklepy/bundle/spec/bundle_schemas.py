# GENERATED FROM spec/bundle-spec.sql — DO NOT EDIT.
# Run `npm run generate` (or node codegen/generate-all.mjs) to refresh.
"""Per-table parquet column descriptors (names, arrow type tokens, nullability).

ArrowType is a string token ("int32" | "int64" | "string" | "float64" | "bool" |
"binary"); the producer maps it to a pyarrow type once. Keeps this generated module
dependency-free. Single source of truth: speckle-bundle-spec/spec/bundle-spec.sql.
"""

from typing import NamedTuple


class ColumnSpec(NamedTuple):
    name: str
    type: str  # arrow type token; see module docstring
    nullable: bool


# table name -> ordered column descriptors (matches the parquet field order producers write).
BY_TABLE: dict[str, list[ColumnSpec]] = {
    "eav": [
        ColumnSpec("object_index", "int32", False),
        ColumnSpec("path_index", "int32", False),
        ColumnSpec("value_string", "string", True),
        ColumnSpec("value_double", "float64", True),
        ColumnSpec("value_boolean", "bool", True),
        ColumnSpec("unit", "string", True),
        ColumnSpec("internal_definition_name", "string", True),
    ],
    "geometries": [
        ColumnSpec("geometryIndex", "int32", False),
        ColumnSpec("content", "binary", True),
        ColumnSpec("id", "string", True),
        ColumnSpec("type", "string", True),
    ],
    "nodes": [
        ColumnSpec("id", "int32", False),
        ColumnSpec("kind", "int32", False),
        ColumnSpec("name", "string", True),
        ColumnSpec("def_ref", "int32", True),
        ColumnSpec("transform", "string", True),
        ColumnSpec("units", "string", True),
        ColumnSpec("subtype", "string", True),
        ColumnSpec("argb", "int32", True),
        ColumnSpec("opacity", "float64", True),
        ColumnSpec("metalness", "float64", True),
        ColumnSpec("roughness", "float64", True),
        ColumnSpec("elevation", "float64", True),
    ],
    "object_type": [
        ColumnSpec("object_index", "int32", False),
        ColumnSpec("type_index", "int32", False),
    ],
    "objects": [
        ColumnSpec("object_index", "int32", False),
        ColumnSpec("application_id", "string", False),
    ],
    "paths": [
        ColumnSpec("path_index", "int32", False),
        ColumnSpec("path", "string", False),
    ],
    "relations": [
        ColumnSpec("rel", "int32", False),
        ColumnSpec("src", "int32", False),
        ColumnSpec("dst", "int32", False),
        ColumnSpec("ord", "int32", True),
    ],
    "scene_views": [
        ColumnSpec("view", "int32", False),
        ColumnSpec("name", "string", True),
        ColumnSpec("is_default", "bool", True),
        ColumnSpec("ord", "int32", True),
        ColumnSpec("source", "string", True),
        ColumnSpec("ref", "string", True),
    ],
    "type_eav": [
        ColumnSpec("type_index", "int32", False),
        ColumnSpec("path_index", "int32", False),
        ColumnSpec("value_string", "string", True),
        ColumnSpec("value_double", "float64", True),
        ColumnSpec("value_boolean", "bool", True),
        ColumnSpec("unit", "string", True),
        ColumnSpec("internal_definition_name", "string", True),
    ],
    "types": [
        ColumnSpec("type_index", "int32", False),
        ColumnSpec("type_key", "string", False),
    ],
}
