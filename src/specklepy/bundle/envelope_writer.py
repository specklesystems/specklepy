"""Envelope topology writer — direct Zstd parquet, one file per table.

Port of the .NET ``EnvelopeWriter``. The table SHAPES and the self-describing catalog
(rel_types / node_kinds / meta) come from the generated ``speckle-bundle-spec`` — this
writer never hand-declares them. ::

  {base}.envelope.relations.parquet(rel, src, dst, ord)  -- typed edges; ns per rel
  {base}.envelope.nodes.parquet(id, kind, name, def_ref,  -- shared value-entities;
        transform, units, subtype, argb, opacity,         -- `subtype` is the CONTAINER
        metalness, roughness, elevation)                  -- discriminator (Model/Coll)
  {base}.envelope.{meta,rel_types,node_kinds}.parquet    -- self-describing catalog
  {base}.envelope.scene_views.parquet(...)               -- producer grouping; omit if 0

``transform`` is 16 row-major doubles, comma-separated. Not thread-safe.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum

import pyarrow as pa

from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import (
    BY_TABLE,
    NODE_KINDS,
    REL_TYPES,
    SCHEMA_VERSION,
)


class ProjectionSource(IntEnum):
    """The store a SceneViewKey reads from: a relation walk or an eav group-by."""

    REL = 0
    EAV = 1


@dataclass(frozen=True)
class SceneViewKey:
    """One ordered key of a SceneView projection.

    For ``REL``, ``ref`` is a rel id as a string; for ``EAV`` it is a bare eav attr
    key.
    Build via :meth:`rel` / :meth:`eav` so ``ref`` is encoded correctly.
    """

    source: ProjectionSource
    ref: str

    @staticmethod
    def rel(rel: int) -> SceneViewKey:
        return SceneViewKey(ProjectionSource.REL, str(int(rel)))

    @staticmethod
    def eav(attr_key: str) -> SceneViewKey:
        return SceneViewKey(ProjectionSource.EAV, attr_key)


@dataclass(frozen=True)
class SceneView:
    """A producer-authored scene-explorer projection (SOT §8).

    Exactly one view per artefact should be ``is_default``; ``keys`` are
    outermost-first. Producers OMIT keys with no data.
    """

    view: int
    name: str
    is_default: bool
    keys: list[SceneViewKey]


class EnvelopeWriter:
    def __init__(self, output_dir: str, base_name: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.base_name = base_name

        self._relations = ParquetTableWriter(
            self._p("relations.parquet"), schema_of(BY_TABLE["relations"])
        )
        self._nodes = ParquetTableWriter(
            self._p("nodes.parquet"), schema_of(BY_TABLE["nodes"])
        )
        self._scene_views: list[SceneView] = []
        self._completed = False

        self._write_catalog()

    @property
    def envelope_db_path(self) -> str:
        return self.output_dir

    def add_relation(self, rel: int, src: int, dst: int, ord: int) -> None:
        """Append one typed edge. ``src``/``dst`` are dense ids in the namespaces
        fixed by ``rel``."""
        self._ensure_not_completed()
        self._relations.add_row(int(rel), src, dst, ord)

    def add_node(
        self,
        id: int,
        kind: int,
        name: str | None,
        def_ref: int | None,
        transform: str | None,
        units: str | None,
        subtype: str | None,
        argb: int | None,
        opacity: float | None,
        metalness: float | None,
        roughness: float | None,
        elevation: float | None,
    ) -> None:
        """Append one value-node. Only the columns relevant to ``kind`` are non-null."""
        self._ensure_not_completed()
        self._nodes.add_row(
            id,
            int(kind),
            name,
            def_ref,
            transform,
            units,
            subtype,
            argb,
            opacity,
            metalness,
            roughness,
            elevation,
        )

    def add_scene_view(self, view: SceneView) -> None:
        """Buffer a producer-authored projection; flushed to scene_views.parquet on
        complete()."""
        self._ensure_not_completed()
        self._scene_views.append(view)

    def complete(self) -> None:
        if self._completed:
            return
        self._completed = True
        self._relations.complete()
        self._nodes.complete()
        self._write_scene_views()

    # Self-describing catalog (SOT §6): rel/kind vocabulary + schema version, from the
    # generated spec catalog (live + reserved rows; retired ids are absent and never
    # reused). Tiny.
    def _write_catalog(self) -> None:
        with ParquetTableWriter(
            self._p("meta.parquet"),
            pa.schema(
                [
                    pa.field("schema_version", pa.int32(), nullable=False),
                    pa.field("produced_by", pa.string()),
                ]
            ),
        ) as meta:
            meta.add_row(SCHEMA_VERSION, "specklepy EnvelopeWriter")

        with ParquetTableWriter(
            self._p("rel_types.parquet"),
            pa.schema(
                [
                    pa.field("rel", pa.int32(), nullable=False),
                    pa.field("name", pa.string()),
                    pa.field("src_ns", pa.string()),
                    pa.field("dst_ns", pa.string()),
                ]
            ),
        ) as rt:
            for r in REL_TYPES:
                if r.status == "retired":
                    continue
                rt.add_row(r.id, r.name, r.src_ns, r.dst_ns)

        with ParquetTableWriter(
            self._p("node_kinds.parquet"),
            pa.schema(
                [
                    pa.field("kind", pa.int32(), nullable=False),
                    pa.field("name", pa.string()),
                ]
            ),
        ) as nk:
            for k in NODE_KINDS:
                if k.status == "retired":
                    continue
                nk.add_row(k.id, k.name)

    def _write_scene_views(self) -> None:
        if not self._scene_views:
            return
        with ParquetTableWriter(
            self._p("scene_views.parquet"), schema_of(BY_TABLE["scene_views"])
        ) as sv:
            for v in self._scene_views:
                for ord, key in enumerate(v.keys):
                    sv.add_row(
                        v.view,
                        v.name,
                        v.is_default,
                        ord,
                        "rel" if key.source == ProjectionSource.REL else "eav",
                        key.ref,
                    )

    def _p(self, suffix: str) -> str:
        return os.path.join(self.output_dir, f"{self.base_name}.envelope.{suffix}")

    def _ensure_not_completed(self) -> None:
        if self._completed:
            raise RuntimeError("Writer already completed.")
