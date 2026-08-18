"""Vendored Speckle bundle spec — the single source of truth, generated.

These two modules (``bundle_spec``, ``bundle_schemas``) are GENERATED from
``speckle-bundle-spec/spec/bundle-spec.sql`` and committed here verbatim (the same
"compiled-in" approach the .NET SDK uses with BundleSpec.cs / BundleSchemas.cs). Do
not hand-edit.

PINNED: ``BUNDLE_SPEC_PIN.json`` records the exact bundle-spec version + spec hash these
files were vendored from, so the C++ extractors (which build against the same published
bundle-spec artifact) and this Python target stay in lockstep. CI enforces it with
``npm run verify-pin -- --python <this dir>`` in the speckle-bundle-spec repo.

To refresh: in a clone of ``speckle-bundle-spec`` at the target version run
``node codegen/generate-all.mjs``, copy ``generated/python/*.py`` over these files, and
update ``BUNDLE_SPEC_PIN.json`` (its ``version`` + ``specHash``).
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
