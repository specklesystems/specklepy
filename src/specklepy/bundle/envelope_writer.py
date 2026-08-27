"""Envelope topology writer — direct Zstd parquet, one file per table.

Port of the .NET ``EnvelopeWriter``. Table shapes and the self-describing catalog
come from the vendored spec in :mod:`specklepy.bundle.spec`. Not thread-safe.
"""

from __future__ import annotations

import importlib.metadata
import os
from dataclasses import dataclass
from enum import IntEnum

import pyarrow as pa

from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import (
    BY_TABLE,
    CAMERA_VIEWS,
    NODE_KINDS,
    NODES,
    REL_TYPES,
    RELATIONS,
    SCENE_VIEWS,
    SCHEMA_VERSION,
)


def _specklepy_version() -> str:
    try:
        return importlib.metadata.version("specklepy")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


@dataclass(frozen=True)
class Producer:
    """Provenance stamped into ``meta``: who produced the bundle, with which SDK."""

    slug: str
    version: str
    sdk_name: str = "specklepy"
    sdk_version: str = _specklepy_version()
    migrated_from_schema_version: int | None = None


class ProjectionSource(IntEnum):
    REL = 0
    EAV = 1


@dataclass(frozen=True)
class SceneViewKey:
    """One ordered SceneView key; ``ref`` is a rel id (REL) or an eav path (EAV)."""

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
    """A producer-authored scene-explorer grouping; ``keys`` outermost-first."""

    view: int
    name: str
    is_default: bool
    keys: list[SceneViewKey]


@dataclass(frozen=True)
class CameraView:
    """Named camera viewpoint; pos/target in ``units``, ``fov`` in vertical degrees."""

    view: int
    name: str | None
    is_default: bool
    ord: int | None
    pos_x: float
    pos_y: float
    pos_z: float
    forward_x: float
    forward_y: float
    forward_z: float
    up_x: float
    up_y: float
    up_z: float
    target_x: float | None = None
    target_y: float | None = None
    target_z: float | None = None
    units: str | None = None
    is_ortho: bool = False
    fov: float | None = None
    lens_mm: float | None = None
    ortho_height: float | None = None
    aspect: float | None = None
    near: float | None = None
    far: float | None = None


_META_SCHEMA = pa.schema(
    [
        pa.field("schema_version", pa.string(), nullable=False),
        pa.field("produced_by", pa.string()),
        pa.field("producer_version", pa.string()),
        pa.field("sdk_name", pa.string()),
        pa.field("sdk_version", pa.string()),
        pa.field("migrated_from_schema_version", pa.int32()),
    ]
)

_REL_TYPES_SCHEMA = pa.schema(
    [
        pa.field("rel", pa.int32(), nullable=False),
        pa.field("name", pa.string()),
        pa.field("src_ns", pa.string()),
        pa.field("dst_ns", pa.string()),
    ]
)

_NODE_KINDS_SCHEMA = pa.schema(
    [
        pa.field("kind", pa.int32(), nullable=False),
        pa.field("name", pa.string()),
    ]
)


class EnvelopeWriter:
    def __init__(self, output_dir: str, base_name: str, producer: Producer) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.base_name = base_name
        self._producer = producer

        self._relations = ParquetTableWriter(
            self._p("relations.parquet"),
            schema_of(BY_TABLE["relations"]),
            table="relations",
            column_count=RELATIONS.COLUMN_COUNT,
        )
        self._nodes = ParquetTableWriter(
            self._p("nodes.parquet"),
            schema_of(BY_TABLE["nodes"]),
            table="nodes",
            column_count=NODES.COLUMN_COUNT,
        )
        self._scene_views: list[SceneView] = []
        self._camera_views: list[CameraView] = []
        self._completed = False

        self._write_catalog()

    def add_relation(self, rel: int, src: int, dst: int, ord: int | None) -> None:
        self._ensure_not_completed()
        self._relations.add_row(int(rel), src, dst, ord)

    def add_node(
        self,
        id: int,
        kind: int,
        *,
        name: str | None = None,
        def_ref: int | None = None,
        transform: str | None = None,
        units: str | None = None,
        subtype: str | None = None,
        argb: int | None = None,
        opacity: float | None = None,
        metalness: float | None = None,
        roughness: float | None = None,
        emissive: int | None = None,
        ior: float | None = None,
        elevation: float | None = None,
        gh_topology: str | None = None,
    ) -> None:
        self._ensure_not_completed()
        self._nodes.add_row_at(
            {
                NODES.ID: id,
                NODES.KIND: int(kind),
                NODES.NAME: name,
                NODES.DEF_REF: def_ref,
                NODES.TRANSFORM: transform,
                NODES.UNITS: units,
                NODES.SUBTYPE: subtype,
                NODES.ARGB: argb,
                NODES.OPACITY: opacity,
                NODES.METALNESS: metalness,
                NODES.ROUGHNESS: roughness,
                NODES.EMISSIVE: emissive,
                NODES.IOR: ior,
                NODES.ELEVATION: elevation,
                NODES.GH_TOPOLOGY: gh_topology,
            }
        )

    def add_scene_view(self, view: SceneView) -> None:
        self._ensure_not_completed()
        self._scene_views.append(view)

    def add_camera_view(self, view: CameraView) -> None:
        self._ensure_not_completed()
        self._camera_views.append(view)

    def complete(self) -> None:
        if self._completed:
            return
        self._completed = True
        self._relations.complete()
        self._nodes.complete()
        self._write_meta()
        self._write_scene_views()
        self._write_camera_views()

    def _write_meta(self) -> None:
        p = self._producer
        with ParquetTableWriter(
            self._p("meta.parquet"), _META_SCHEMA, table="meta"
        ) as meta:
            meta.add_row(
                SCHEMA_VERSION,
                p.slug,
                p.version,
                p.sdk_name,
                p.sdk_version,
                p.migrated_from_schema_version,
            )

    def _write_catalog(self) -> None:
        with ParquetTableWriter(
            self._p("rel_types.parquet"), _REL_TYPES_SCHEMA, table="rel_types"
        ) as rt:
            for r in REL_TYPES:
                if r.status != "retired":
                    rt.add_row(r.id, r.name, r.src_ns, r.dst_ns)

        with ParquetTableWriter(
            self._p("node_kinds.parquet"), _NODE_KINDS_SCHEMA, table="node_kinds"
        ) as nk:
            for k in NODE_KINDS:
                if k.status != "retired":
                    nk.add_row(k.id, k.name)

    def _write_scene_views(self) -> None:
        if not self._scene_views:
            return
        with ParquetTableWriter(
            self._p("scene_views.parquet"),
            schema_of(BY_TABLE["scene_views"]),
            table="scene_views",
            column_count=SCENE_VIEWS.COLUMN_COUNT,
        ) as sv:
            for v in self._scene_views:
                for ord, key in enumerate(v.keys):
                    sv.add_row_at(
                        {
                            SCENE_VIEWS.VIEW: v.view,
                            SCENE_VIEWS.NAME: v.name,
                            SCENE_VIEWS.IS_DEFAULT: v.is_default,
                            SCENE_VIEWS.ORD: ord,
                            SCENE_VIEWS.SOURCE: (
                                "rel" if key.source == ProjectionSource.REL else "eav"
                            ),
                            SCENE_VIEWS.REF: key.ref,
                        }
                    )

    def _write_camera_views(self) -> None:
        if not self._camera_views:
            return
        with ParquetTableWriter(
            self._p("camera_views.parquet"),
            schema_of(BY_TABLE["camera_views"]),
            table="camera_views",
            column_count=CAMERA_VIEWS.COLUMN_COUNT,
        ) as cv:
            for v in self._camera_views:
                cv.add_row_at(
                    {
                        CAMERA_VIEWS.VIEW: v.view,
                        CAMERA_VIEWS.NAME: v.name,
                        CAMERA_VIEWS.IS_DEFAULT: v.is_default,
                        CAMERA_VIEWS.ORD: v.ord,
                        CAMERA_VIEWS.POS_X: v.pos_x,
                        CAMERA_VIEWS.POS_Y: v.pos_y,
                        CAMERA_VIEWS.POS_Z: v.pos_z,
                        CAMERA_VIEWS.FORWARD_X: v.forward_x,
                        CAMERA_VIEWS.FORWARD_Y: v.forward_y,
                        CAMERA_VIEWS.FORWARD_Z: v.forward_z,
                        CAMERA_VIEWS.UP_X: v.up_x,
                        CAMERA_VIEWS.UP_Y: v.up_y,
                        CAMERA_VIEWS.UP_Z: v.up_z,
                        CAMERA_VIEWS.TARGET_X: v.target_x,
                        CAMERA_VIEWS.TARGET_Y: v.target_y,
                        CAMERA_VIEWS.TARGET_Z: v.target_z,
                        CAMERA_VIEWS.UNITS: v.units,
                        CAMERA_VIEWS.IS_ORTHO: v.is_ortho,
                        CAMERA_VIEWS.FOV: v.fov,
                        CAMERA_VIEWS.LENS_MM: v.lens_mm,
                        CAMERA_VIEWS.ORTHO_HEIGHT: v.ortho_height,
                        CAMERA_VIEWS.ASPECT: v.aspect,
                        CAMERA_VIEWS.NEAR: v.near,
                        CAMERA_VIEWS.FAR: v.far,
                    }
                )

    def _p(self, suffix: str) -> str:
        return os.path.join(self.output_dir, f"{self.base_name}.envelope.{suffix}")

    def _ensure_not_completed(self) -> None:
        if self._completed:
            raise RuntimeError("Writer already completed.")
