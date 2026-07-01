# GENERATED FROM spec/bundle-spec.sql — DO NOT EDIT.
# Run `npm run generate` (or node codegen/generate-all.mjs) to refresh.
"""Speckle bundle vocabulary (schema_version 5).

Single source of truth: speckle-bundle-spec/spec/bundle-spec.sql. Regenerate with
`node codegen/generate-all.mjs` in that repo, then re-vendor into specklepy.
"""

from enum import IntEnum
from typing import NamedTuple, Optional

SCHEMA_VERSION = 5


class Rel(IntEnum):
    """Live relation ids (typed envelope edges)."""

    DISPLAY = 1
    SOLID = 2
    SUBELEMENT = 3
    DEFINES = 4
    HAS_MATERIAL = 5
    HAS_COLOR = 6
    ON_LEVEL = 7
    DISPLAY_INSTANCE = 8
    DEFINES_INSTANCE = 9
    IN_COLLECTION = 10
    IN_MODEL = 11
    IN_ROOM = 12
    IN_SYSTEM = 14
    CONNECTS_TO = 21
    BOUNDS = 23


class NodeKind(IntEnum):
    """Live node-kind ids (synthetic envelope nodes)."""

    DEFINITION = 1
    INSTANCE = 2
    MATERIAL = 3
    COLOR = 4
    LEVEL = 5
    CONTAINER = 7


class RelTypeRow(NamedTuple):
    id: int
    name: str
    src_ns: Optional[str]
    dst_ns: Optional[str]
    status: str
    ord_semantics: Optional[str]


class NodeKindRow(NamedTuple):
    id: int
    name: str
    status: str
    subtype_values: Optional[str]


# Full catalogs incl. reserved/retired rows (ids are retired in place, never reused),
# shipped in the bundle as the self-describing rel_types / node_kinds tables.
REL_TYPES: list[RelTypeRow] = [
    RelTypeRow(1, "DISPLAY", "object", "geometry", "live", "ordinal"),
    RelTypeRow(2, "SOLID", "object", "geometry", "reserved", "ordinal"),
    RelTypeRow(3, "SUBELEMENT", "object", "object", "live", "ordinal"),
    RelTypeRow(4, "DEFINES", "node", "geometry", "live", None),
    RelTypeRow(5, "HAS_MATERIAL", "geometry", "node", "live", None),
    RelTypeRow(6, "HAS_COLOR", "geometry|object", "node", "live", None),
    RelTypeRow(7, "ON_LEVEL", "object", "node", "live", None),
    RelTypeRow(8, "DISPLAY_INSTANCE", "object", "node", "live", "ordinal"),
    RelTypeRow(9, "DEFINES_INSTANCE", "node", "node", "live", "ordinal"),
    RelTypeRow(10, "IN_COLLECTION", "object", "node", "live", None),
    RelTypeRow(11, "IN_MODEL", "object", "node", "live", None),
    RelTypeRow(12, "IN_ROOM", "object", "object", "live", None),
    RelTypeRow(13, "IN_SPACE", None, None, "retired", None),
    RelTypeRow(14, "IN_SYSTEM", "object", "node", "live", None),
    RelTypeRow(15, "IN_NETWORK", None, None, "retired", None),
    RelTypeRow(16, "IN_LINE", None, None, "retired", None),
    RelTypeRow(17, "IN_GROUP", None, None, "retired", None),
    RelTypeRow(18, "IN_ASSEMBLY", None, None, "retired", None),
    RelTypeRow(19, "IN_SUBASSEMBLY", None, None, "retired", None),
    RelTypeRow(20, "XREF", None, None, "retired", None),
    RelTypeRow(21, "CONNECTS_TO", "object", "object", "live", "scope"),
    RelTypeRow(22, "HOSTED_ON", None, None, "retired", None),
    RelTypeRow(23, "BOUNDS", "object", "object", "live", None),
]

NODE_KINDS: list[NodeKindRow] = [
    NodeKindRow(1, "DEFINITION", "live", None),
    NodeKindRow(2, "INSTANCE", "live", None),
    NodeKindRow(3, "MATERIAL", "live", None),
    NodeKindRow(4, "COLOR", "live", None),
    NodeKindRow(5, "LEVEL", "live", None),
    NodeKindRow(6, "COLLECTION", "retired", None),
    NodeKindRow(7, "CONTAINER", "live", "Collection,Model,MEP System,Network"),
]
