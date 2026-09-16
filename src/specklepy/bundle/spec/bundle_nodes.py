# GENERATED FROM spec/bundle-spec.sql — DO NOT EDIT.
# Run `npm run generate` (or node codegen/generate-all.mjs) to refresh.
"""One record per live node kind, carrying exactly the nodes.* columns it declares.

Single source of truth: speckle-bundle-spec/spec/bundle-spec.sql (node_kinds.columns).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    """Shared geometry template."""

    name: str | None = None
    def_ref: int | None = None


@dataclass(frozen=True)
class Instance:
    """A placement / occurrence."""

    transform: str
    def_ref: int
    units: str | None = None


@dataclass(frozen=True)
class Material:
    """Full-PBR render asset."""

    argb: int
    opacity: float
    metalness: float
    roughness: float
    name: str | None = None
    emissive: int | None = None
    ior: float | None = None


@dataclass(frozen=True)
class Color:
    """Raw colour override."""

    argb: int


@dataclass(frozen=True)
class Level:
    """A storey."""

    elevation: float
    name: str | None = None


@dataclass(frozen=True)
class Container:
    """Polymorphic grouping tree."""

    subtype: str
    name: str | None = None
    def_ref: int | None = None
    gh_topology: str | None = None
