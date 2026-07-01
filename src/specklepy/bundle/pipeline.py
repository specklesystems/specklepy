"""Speckle 4.0 bundle producer — the typed emit API a converter drives.

Port of the .NET ``ObjectsArtifactPipeline``. PARQUET-ONLY: direct Zstd parquet,
one file per table, no DuckDB. Owns the three per-namespace identity interners and
exposes a typed emit API so the producer stays string-based while the artefacts
store pure dense int32:

* **object** namespace — interned by the eav writer (eav is the dictionary home);
  resolved here via :meth:`intern_object`.
* **geometry** namespace — :attr:`_geometry_interner`; one row per mesh.
* **node** namespace — :attr:`_node_interner` (kind-prefixed keys); definitions /
  instances / materials / colours / levels / containers.

Producing the files is decoupled from uploading: write here (:meth:`complete`), then
hand the output dir to the uploader (:mod:`specklepy.bundle.upload`).
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from specklepy.bundle import sgeo
from specklepy.bundle.eav_extraction import (
    DEFAULT_EXCLUDED_TOP_LEVEL,
    flatten_properties,
    flatten_subtree,
)
from specklepy.bundle.eav_writer import EavWriter
from specklepy.bundle.envelope_writer import EnvelopeWriter, SceneView
from specklepy.bundle.geometries_writer import GeometriesParquetWriter
from specklepy.bundle.interner import IdInterner
from specklepy.bundle.spec import NodeKind, Rel


def _format_transform(transform: Sequence[float]) -> str:
    """16 row-major doubles as a comma-separated string (consumer parses to f64)."""
    return ",".join(repr(float(d)) for d in transform)


def _argb_int32(argb: int) -> int:
    """Reinterpret a packed ARGB colour as a signed int32 (the `argb` column type).

    Producers often hold ARGB as an unsigned 32-bit int (0..2^32-1); the bundle
    stores the SAME 32 bits as a signed int32 (matching the .NET ``int`` storage),
    so the high-alpha bit becomes the sign. Identity for values already in signed
    range.
    """
    argb &= 0xFFFFFFFF
    return argb - 0x1_0000_0000 if argb >= 0x8000_0000 else argb


class ObjectsArtifactPipeline:
    def __init__(
        self,
        output_dir: str,
        base_name: str,
        excluded_top_level_properties: set[str] | None = None,
    ) -> None:
        self._geometries = GeometriesParquetWriter(output_dir, base_name)
        self._envelope = EnvelopeWriter(output_dir, base_name)
        self._eav = EavWriter(output_dir, base_name)
        self._excluded = (
            excluded_top_level_properties
            if excluded_top_level_properties is not None
            else set(DEFAULT_EXCLUDED_TOP_LEVEL)
        )

        # per-namespace interners. The object namespace is owned by the eav writer
        # (it writes the dictionary), so it is not duplicated here.
        self._geometry_interner = IdInterner()
        self._node_interner = IdInterner()

        self.output_dir = output_dir
        self.base_name = base_name

    @property
    def geometries_path(self) -> str:
        return self._geometries.geometries_path

    # ── object namespace ────────────────────────────────────────────────────

    def intern_object(self, application_id: str) -> int:
        """Resolve an object's dense K (interns its applicationId via eav dict)."""
        return self._eav.get_or_add_object(application_id)

    def add_properties(
        self,
        application_id: str,
        properties: Mapping[str, Any],
        root_scalars: Iterable[tuple[str, Any]] | None = None,
        type_key: str | None = None,
    ) -> None:
        """Flatten an object's property tree into ``eav`` keyed by ``application_id``.

        When ``type_key`` is given and there are type-scoped Parameters, those are
        deduped into ``type_eav`` (once per type) with an ``object_type`` weak ref;
        otherwise everything flattens per-object.
        """
        split = _try_split_type_parameters(properties) if type_key is not None else None
        if split is None:
            rows = flatten_properties(
                application_id, properties, root_scalars, self._excluded
            )
            self._eav.add_rows(application_id, rows)
            return

        instance_props, type_subtree = split
        instance_rows = flatten_properties(
            application_id, instance_props, root_scalars, self._excluded
        )
        self._eav.add_rows(application_id, instance_rows)
        self._eav.add_type(
            application_id,
            type_key,
            lambda: flatten_subtree(type_subtree, "properties.Parameters"),
        )

    # ── geometry namespace ──────────────────────────────────────────────────

    def add_geometry(self, mesh_application_id: str, geometry: Any) -> int:
        """Intern a mesh's applicationId to a dense geometry K, encoding + storing
        its SGEO blob on first sight. Returns the K (for DISPLAY/DEFINES/HAS_MATERIAL
        edges)."""
        k, is_new = self._geometry_interner.get_or_add(mesh_application_id)
        if is_new:
            self._geometries.add_geometry(k, sgeo.encode(geometry))
        return k

    def add_raw_geometry(
        self, geometry_application_id: str, content: bytes, type_label: str
    ) -> int:
        """Intern + store RAW bytes verbatim (no SGEO encoding) with a type label."""
        k, is_new = self._geometry_interner.get_or_add(geometry_application_id)
        if is_new:
            self._geometries.add_raw_geometry(k, content, type_label)
        return k

    def intern_geometry_id(self, mesh_application_id: str) -> int:
        """Resolve the geometry K for an already-added mesh (lookup, no encode)."""
        return self._geometry_interner.intern(mesh_application_id)

    # ── node namespace (value-entities) ─────────────────────────────────────

    def add_definition(self, definition_key: str, name: str | None) -> int:
        """Intern a DEFINITION node (instance-definition / block), writing it once."""
        k, is_new = self._node_interner.get_or_add("def:" + definition_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.DEFINITION,
                name,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        return k

    def add_instance(
        self,
        placement_key: str,
        def_ref: int,
        transform: Sequence[float],
        units: str | None,
    ) -> int:
        """Intern an INSTANCE (placement) node — its transform (16 row-major
        doubles) + DEFINITION."""
        k, is_new = self._node_interner.get_or_add("inst:" + placement_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.INSTANCE,
                None,
                def_ref,
                _format_transform(transform),
                units,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        return k

    def add_material(
        self,
        material_key: str,
        argb: int,
        opacity: float,
        metalness: float,
        roughness: float,
    ) -> int:
        """Intern a MATERIAL value-node (inline render value), writing it once."""
        k, is_new = self._node_interner.get_or_add("mat:" + material_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.MATERIAL,
                None,
                None,
                None,
                None,
                None,
                _argb_int32(argb),
                opacity,
                metalness,
                roughness,
                None,
            )
        return k

    def add_color(self, argb: int) -> int:
        """Intern a COLOR value-node (keyed by its argb), writing it once."""
        signed = _argb_int32(argb)
        k, is_new = self._node_interner.get_or_add("col:" + str(signed))
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.COLOR,
                None,
                None,
                None,
                None,
                None,
                signed,
                None,
                None,
                None,
                None,
            )
        return k

    def add_level(self, level_key: str, name: str | None, elevation: float) -> int:
        """Intern a LEVEL value-node (name + elevation), writing it once."""
        k, is_new = self._node_interner.get_or_add("lvl:" + level_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.LEVEL,
                name,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                elevation,
            )
        return k

    def add_collection(
        self,
        collection_key: str,
        name: str | None,
        parent_collection_k: int | None,
        subtype: str | None,
    ) -> int:
        """Intern a scene-tree collection (layer / category / story) node, once.

        v5: a collection is a CONTAINER whose ``subtype`` carries its tag; the
        IN_COLLECTION rel marks the grouping axis. ``parent_collection_k`` is its
        parent collection node (None = top-level) — the parent chain IS the source
        hierarchy.
        """
        k, is_new = self._node_interner.get_or_add("coll:" + collection_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.CONTAINER,
                name,
                parent_collection_k,
                None,
                None,
                subtype,
                None,
                None,
                None,
                None,
                None,
            )
        return k

    def add_container(
        self,
        container_key: str,
        name: str | None,
        parent_container_k: int | None,
        subtype: str | None,
    ) -> int:
        """Intern a CONTAINER (semantic-topology bucket: model / room / system / …)
        node, once.

        Distinct from :meth:`add_collection` (the authored scene-tree). ``subtype`` is
        the canonical axis tag (e.g. "Model", "System") — use the SAME tag across
        connectors for the same concept.
        """
        k, is_new = self._node_interner.get_or_add("cont:" + container_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.CONTAINER,
                name,
                parent_container_k,
                None,
                None,
                subtype,
                None,
                None,
                None,
                None,
                None,
            )
        return k

    # ── relations ───────────────────────────────────────────────────────────

    def display(self, object_k: int, geometry_k: int, ord: int) -> None:
        """object → geometry: direct renderable geometry (world-coord mesh)."""
        self._envelope.add_relation(Rel.DISPLAY, object_k, geometry_k, ord)

    def display_instance(self, object_k: int, instance_k: int, ord: int) -> None:
        """object → node(INSTANCE): renderable via a placement (transform + def)."""
        self._envelope.add_relation(Rel.DISPLAY_INSTANCE, object_k, instance_k, ord)

    def solid(self, object_k: int, geometry_k: int, ord: int) -> None:
        """object → geometry: authoritative solid."""
        self._envelope.add_relation(Rel.SOLID, object_k, geometry_k, ord)

    def subelement(self, parent_object_k: int, child_object_k: int, ord: int) -> None:
        """object → object: host→hosted (curtain wall → panel)."""
        self._envelope.add_relation(
            Rel.SUBELEMENT, parent_object_k, child_object_k, ord
        )

    def defines(self, definition_k: int, geometry_k: int, ord: int) -> None:
        """node(DEFINITION) → geometry: definition contains a raw mesh member."""
        self._envelope.add_relation(Rel.DEFINES, definition_k, geometry_k, ord)

    def defines_instance(self, definition_k: int, instance_k: int, ord: int) -> None:
        """node(DEFINITION) → node(nested INSTANCE): definition contains a nested
        block placement."""
        self._envelope.add_relation(Rel.DEFINES_INSTANCE, definition_k, instance_k, ord)

    def has_material(self, geometry_k: int, material_k: int) -> None:
        """geometry → node(MATERIAL): per-mesh render material."""
        self._envelope.add_relation(Rel.HAS_MATERIAL, geometry_k, material_k, 0)

    def has_color(self, src_k: int, color_k: int) -> None:
        """geometry | object → node(COLOR): display colour."""
        self._envelope.add_relation(Rel.HAS_COLOR, src_k, color_k, 0)

    def on_level(self, object_k: int, level_k: int) -> None:
        """object → node(LEVEL): level membership."""
        self._envelope.add_relation(Rel.ON_LEVEL, object_k, level_k, 0)

    def in_collection(self, object_k: int, collection_k: int, ord: int) -> None:
        """object → node(COLLECTION): direct membership in a scene-tree container."""
        self._envelope.add_relation(Rel.IN_COLLECTION, object_k, collection_k, ord)

    def in_model(self, object_k: int, model_k: int, ord: int) -> None:
        """object → node(CONTAINER, subtype "Model"): source-document / host /
        linked-model membership."""
        self._envelope.add_relation(Rel.IN_MODEL, object_k, model_k, ord)

    def in_room(self, object_k: int, room_k: int, ord: int) -> None:
        """object → node(CONTAINER, subtype "Room"): room containment."""
        self._envelope.add_relation(Rel.IN_ROOM, object_k, room_k, ord)

    def in_system(self, object_k: int, system_k: int, ord: int) -> None:
        """object → node(CONTAINER, subtype "System"): named logical engineering
        system membership.

        Also the v5 home of physically-connected NETWORKS (subtype "Network") —
        IN_NETWORK was collapsed into IN_SYSTEM.
        """
        self._envelope.add_relation(Rel.IN_SYSTEM, object_k, system_k, ord)

    def connects_to(
        self, source_object_k: int, target_object_k: int, ord: int = 0
    ) -> None:
        """object → object: physical flow connectivity, DIRECTED src→dst by flow.

        A reciprocal pair (a→b AND b→a) encodes undirected / unknown flow. ``ord`` is
        the scope tag (system-K, or 0 = unscoped).
        """
        self._envelope.add_relation(
            Rel.CONNECTS_TO, source_object_k, target_object_k, ord
        )

    # ── scene views ─────────────────────────────────────────────────────────

    def add_scene_view(self, view: SceneView) -> None:
        """Author a scene_views projection (SOT §8): the producer's default grouping."""
        self._envelope.add_scene_view(view)

    # ── lifecycle ───────────────────────────────────────────────────────────

    def complete(self) -> None:
        """Flush + finalize every artefact. All parquet files written on return."""
        self._geometries.complete()
        self._envelope.complete()
        self._eav.complete()

    def __enter__(self) -> ObjectsArtifactPipeline:
        return self

    def __exit__(self, *exc: object) -> None:
        self.complete()


# Splits `properties.Parameters` into instance-scoped (kept on the object) and
# type-scoped (Type + System Parameters, deduped per type). Returns None if there's
# nothing type-scoped.
def _try_split_type_parameters(
    properties: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    params = properties.get("Parameters")
    if not isinstance(params, Mapping):
        return None

    type_params: dict[str, Any] = {}
    instance_params: dict[str, Any] = {}
    for key, value in params.items():
        if key in ("Type Parameters", "System Type Parameters"):
            type_params[key] = value
        else:
            instance_params[key] = value

    if not type_params:
        return None

    merged = dict(properties)
    merged["Parameters"] = instance_params
    return merged, type_params
