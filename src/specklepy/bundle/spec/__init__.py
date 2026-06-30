"""Vendored Speckle bundle spec — the single source of truth, generated.

These two modules (``bundle_spec``, ``bundle_schemas``) are GENERATED from
``speckle-bundle-spec/spec/bundle-spec.sql`` and committed here verbatim (the same
"compiled-in" approach the .NET SDK uses with BundleSpec.cs / BundleSchemas.cs). Do
not hand-edit. To refresh: in a sibling clone of ``speckle-bundle-spec`` run
``node codegen/generate-all.mjs`` and copy ``generated/python/*.py`` over these files.
"""

from specklepy.bundle.spec.bundle_schemas import BY_TABLE, ColumnSpec
from specklepy.bundle.spec.bundle_spec import (
    NODE_KINDS,
    REL_TYPES,
    SCHEMA_VERSION,
    NodeKind,
    NodeKindRow,
    Rel,
    RelTypeRow,
)

__all__ = [
    "BY_TABLE",
    "ColumnSpec",
    "NODE_KINDS",
    "REL_TYPES",
    "SCHEMA_VERSION",
    "NodeKind",
    "NodeKindRow",
    "Rel",
    "RelTypeRow",
]
