"""Speckle bundle spec — the generated Python target, pulled from the sibling checkout.

``bundle_spec``, ``bundle_schemas`` and ``bundle_cols`` are GENERATED from
``speckle-bundle-spec/spec/bundle-spec.sql``. They are NOT committed here: ``hatch_build.py``
copies them from ``../speckle-bundle-spec/generated/python/`` (or ``$SPECKLE_BUNDLE_SPEC_DIR``)
on every build — the same compiled-in approach the .NET SDK uses with BundleSpec.cs, where
the csproj includes the sibling clone's generated files. The wheel ships them; a dev checkout
gets them on ``uv sync``. Which spec commit CI builds against is pinned in
``.github/actions/checkout-bundle-spec/action.yml`` — the one pin for this repo.
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
