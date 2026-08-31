"""Speckle 4.0 bundle producer — the typed emit API a converter drives.

Port of the .NET ``ObjectsArtifactPipeline``. Parquet-only, one file per table.
Owns the three per-namespace identity interners (object — via the eav writer;
geometry; node) so producers stay string-keyed while the artefacts store dense int32.

Producing is decoupled from uploading: :meth:`ObjectsArtifactPipeline.complete` here,
then hand the output dir to :mod:`specklepy.bundle.upload`.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from specklepy.bundle import sgeo
from specklepy.bundle.eav_extraction import (
    DEFAULT_EXCLUDED_TOP_LEVEL,
    flatten_properties,
    flatten_subtree,
)
from specklepy.bundle.eav_writer import EavWriter
from specklepy.bundle.envelope_writer import (
    CameraView,
    EnvelopeWriter,
    Producer,
    SceneView,
)
from specklepy.bundle.geometries_writer import GeometriesParquetWriter
from specklepy.bundle.interner import IdInterner
from specklepy.bundle.model_eav_writer import ModelEavWriter
from specklepy.bundle.property_set_definitions_writer import (
    PropertySetDefinitionsWriter,
)
from specklepy.bundle.spec import NodeKind, Rel


def _format_transform(transform: Sequence[float]) -> str:
    """16 row-major doubles as a comma-separated string."""
    if len(transform) != 16:
        raise ValueError(f"transform must have 16 doubles, got {len(transform)}")
    return ",".join(repr(float(d)) for d in transform)


def _argb_int32(argb: int) -> int:
    """Reinterpret packed ARGB as signed int32 (the ``argb`` column type)."""
    argb &= 0xFFFFFFFF
    return argb - 0x1_0000_0000 if argb >= 0x8000_0000 else argb


class ObjectsArtifactPipeline:
    def __init__(
        self,
        output_dir: str,
        base_name: str,
        producer: Producer,
        excluded_top_level_properties: set[str] | None = None,
    ) -> None:
        self._geometries = GeometriesParquetWriter(output_dir, base_name)
        self._envelope = EnvelopeWriter(output_dir, base_name, producer)
        self._eav = EavWriter(output_dir, base_name)
        self._model: ModelEavWriter | None = None
        self._property_sets: PropertySetDefinitionsWriter | None = None
        self._excluded = (
            excluded_top_level_properties
            if excluded_top_level_properties is not None
            else set(DEFAULT_EXCLUDED_TOP_LEVEL)
        )

        self._geometry_interner = IdInterner()
        self._node_interner = IdInterner()

        self.output_dir = output_dir
        self.base_name = base_name

    @property
    def geometries_path(self) -> str:
        return self._geometries.geometries_path

    # ── object namespace ────────────────────────────────────────────────────

    def intern_object(self, application_id: str) -> int:
        return self._eav.get_or_add_object(application_id)

    def add_properties(
        self,
        application_id: str,
        properties: Mapping[str, Any],
        root_scalars: Iterable[tuple[str, Any]] | None = None,
        type_key: str | None = None,
    ) -> None:
        """Flatten an object's property tree into ``eav``.

        With ``type_key``, type-scoped Parameters are deduped into ``type_eav`` once
        per type and linked via ``object_type``.
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

    def add_geometry(self, geometry_application_id: str, geometry: Any) -> int:
        """Intern a geometry to a dense K, SGEO-encoding it on first sight."""
        k, is_new = self._geometry_interner.get_or_add(geometry_application_id)
        if is_new:
            self._geometries.add_geometry(k, sgeo.encode(geometry))
        return k

    def add_raw_geometry(
        self, geometry_application_id: str, content: bytes, type_label: str
    ) -> int:
        """Intern + store raw bytes verbatim (no SGEO encoding) under ``type_label``."""
        k, is_new = self._geometry_interner.get_or_add(geometry_application_id)
        if is_new:
            self._geometries.add_raw_geometry(k, content, type_label)
        return k

    def intern_geometry_id(self, geometry_application_id: str) -> int:
        return self._geometry_interner.intern(geometry_application_id)

    # ── node namespace ──────────────────────────────────────────────────────

    def add_definition(self, definition_key: str, name: str | None) -> int:
        k, is_new = self._node_interner.get_or_add("def:" + definition_key)
        if is_new:
            self._envelope.add_node(k, NodeKind.DEFINITION, name=name)
        return k

    def add_instance(
        self,
        placement_key: str,
        def_ref: int,
        transform: Sequence[float],
        units: str | None,
    ) -> int:
        """INSTANCE node: 16 row-major doubles placing ``def_ref``."""
        k, is_new = self._node_interner.get_or_add("inst:" + placement_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.INSTANCE,
                def_ref=def_ref,
                transform=_format_transform(transform),
                units=units,
            )
        return k

    def add_material(
        self,
        material_key: str,
        argb: int,
        opacity: float,
        metalness: float,
        roughness: float,
        *,
        name: str | None = None,
        emissive: int | None = None,
        ior: float | None = None,
    ) -> int:
        """MATERIAL node. ``name`` is the authored host material name."""
        k, is_new = self._node_interner.get_or_add("mat:" + material_key)
        if is_new:
            # spec: black-RGB emissive is stored as NULL (no emission)
            if emissive is not None and emissive & 0x00FFFFFF == 0:
                emissive = None
            self._envelope.add_node(
                k,
                NodeKind.MATERIAL,
                name=name,
                argb=_argb_int32(argb),
                opacity=opacity,
                metalness=metalness,
                roughness=roughness,
                emissive=None if emissive is None else _argb_int32(emissive),
                ior=ior,
            )
        return k

    def add_color(self, argb: int) -> int:
        signed = _argb_int32(argb)
        k, is_new = self._node_interner.get_or_add("col:" + str(signed))
        if is_new:
            self._envelope.add_node(k, NodeKind.COLOR, argb=signed)
        return k

    def add_level(self, level_key: str, name: str | None, elevation: float) -> int:
        k, is_new = self._node_interner.get_or_add("lvl:" + level_key)
        if is_new:
            self._envelope.add_node(k, NodeKind.LEVEL, name=name, elevation=elevation)
        return k

    def add_collection(
        self,
        collection_key: str,
        name: str | None,
        parent_collection_k: int | None,
        subtype: str | None,
        *,
        gh_topology: str | None = None,
    ) -> int:
        """Scene-tree CONTAINER (target of IN_COLLECTION); parent chain via ``def_ref``.

        Spec subtypes: Collection, Layer, Folder, Model, MEP System, Network, Group.
        """
        k, is_new = self._node_interner.get_or_add("coll:" + collection_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.CONTAINER,
                name=name,
                def_ref=parent_collection_k,
                subtype=subtype,
                gh_topology=gh_topology,
            )
        return k

    def add_container(
        self,
        container_key: str,
        name: str | None,
        parent_container_k: int | None,
        subtype: str | None,
    ) -> int:
        """Semantic CONTAINER (Model / MEP System / Network / Group …), distinct from
        the scene tree."""
        k, is_new = self._node_interner.get_or_add("cont:" + container_key)
        if is_new:
            self._envelope.add_node(
                k,
                NodeKind.CONTAINER,
                name=name,
                def_ref=parent_container_k,
                subtype=subtype,
            )
        return k

    # ── relations ───────────────────────────────────────────────────────────

    def display(self, object_k: int, geometry_k: int, ord: int) -> None:
        """object → geometry: world-space renderable."""
        self._envelope.add_relation(Rel.DISPLAY, object_k, geometry_k, ord)

    def display_instance(self, object_k: int, instance_k: int, ord: int) -> None:
        """object → INSTANCE: top-level render root via a placement."""
        self._envelope.add_relation(Rel.DISPLAY_INSTANCE, object_k, instance_k, ord)

    def solid(self, object_k: int, geometry_k: int, ord: int) -> None:
        """object → geometry: authoritative solid."""
        self._envelope.add_relation(Rel.SOLID, object_k, geometry_k, ord)

    def subelement(self, parent_object_k: int, child_object_k: int, ord: int) -> None:
        """object → object: component ownership (curtain wall → panel)."""
        self._envelope.add_relation(
            Rel.SUBELEMENT, parent_object_k, child_object_k, ord
        )

    def defines(self, definition_k: int, geometry_k: int, ord: int) -> None:
        """DEFINITION → geometry; ``ord`` is the member ordinal shared with
        ``defines_instance`` / ``defines_member``."""
        self._envelope.add_relation(Rel.DEFINES, definition_k, geometry_k, ord)

    def defines_instance(self, definition_k: int, instance_k: int, ord: int) -> None:
        """DEFINITION → nested INSTANCE member."""
        self._envelope.add_relation(Rel.DEFINES_INSTANCE, definition_k, instance_k, ord)

    def defines_member(self, definition_k: int, object_k: int, ord: int) -> None:
        """DEFINITION → member object; emitted for every member, never a render root."""
        self._envelope.add_relation(Rel.DEFINES_MEMBER, definition_k, object_k, ord)

    def places(self, object_k: int, instance_k: int) -> None:
        """member object → its INSTANCE node (association only)."""
        self._envelope.add_relation(Rel.PLACES, object_k, instance_k, 0)

    def has_material(self, geometry_k: int, material_k: int) -> None:
        """geometry → MATERIAL."""
        self._envelope.add_relation(Rel.HAS_MATERIAL, geometry_k, material_k, 0)

    def has_color(self, geometry_k: int, color_k: int) -> None:
        """geometry → COLOR."""
        self._envelope.add_relation(Rel.HAS_COLOR, geometry_k, color_k, 0)

    def object_has_material(self, object_k: int, material_k: int) -> None:
        """object → MATERIAL; fills geometry without its own material."""
        self._envelope.add_relation(Rel.OBJECT_HAS_MATERIAL, object_k, material_k, 0)

    def object_has_color(self, object_k: int, color_k: int) -> None:
        """object → COLOR; overrides geometry colour."""
        self._envelope.add_relation(Rel.OBJECT_HAS_COLOR, object_k, color_k, 0)

    def node_has_material(self, node_k: int, material_k: int) -> None:
        """CONTAINER → MATERIAL: authored layer/tag material (weakest tier)."""
        self._envelope.add_relation(Rel.NODE_HAS_MATERIAL, node_k, material_k, 0)

    def node_has_color(self, node_k: int, color_k: int) -> None:
        """CONTAINER → COLOR: authored layer/tag colour (weakest tier)."""
        self._envelope.add_relation(Rel.NODE_HAS_COLOR, node_k, color_k, 0)

    def on_level(self, object_k: int, level_k: int) -> None:
        self._envelope.add_relation(Rel.ON_LEVEL, object_k, level_k, 0)

    def in_collection(self, object_k: int, collection_k: int, ord: int) -> None:
        self._envelope.add_relation(Rel.IN_COLLECTION, object_k, collection_k, ord)

    def in_model(self, object_k: int, model_k: int, ord: int) -> None:
        self._envelope.add_relation(Rel.IN_MODEL, object_k, model_k, ord)

    def in_room(self, object_k: int, room_k: int, ord: int) -> None:
        self._envelope.add_relation(Rel.IN_ROOM, object_k, room_k, ord)

    def in_system(self, object_k: int, system_k: int, ord: int) -> None:
        """object → CONTAINER(MEP System); multi-valued — one edge per membership."""
        self._envelope.add_relation(Rel.IN_SYSTEM, object_k, system_k, ord)

    def in_group(self, object_k: int, group_k: int, ord: int) -> None:
        """object → CONTAINER(Group); multi-valued, independent of IN_COLLECTION."""
        self._envelope.add_relation(Rel.IN_GROUP, object_k, group_k, ord)

    def in_assembly(self, member_k: int, assembly_k: int, ord: int) -> None:
        """member object → assembly object; ``ord == 0`` marks the main member."""
        self._envelope.add_relation(Rel.IN_ASSEMBLY, member_k, assembly_k, ord)

    def hosted_on(self, hosted_k: int, host_k: int) -> None:
        """hosted object → host object (door → wall)."""
        self._envelope.add_relation(Rel.HOSTED_ON, hosted_k, host_k, 0)

    def bounds(self, object_k: int, bounded_k: int, ord: int) -> None:
        self._envelope.add_relation(Rel.BOUNDS, object_k, bounded_k, ord)

    def connects_to(
        self, source_object_k: int, target_object_k: int, ord: int = 0
    ) -> None:
        """object → object, directed by flow; ``ord`` is the scope (system K or 0)."""
        self._envelope.add_relation(
            Rel.CONNECTS_TO, source_object_k, target_object_k, ord
        )

    # ── views ───────────────────────────────────────────────────────────────

    def add_scene_view(self, view: SceneView) -> None:
        self._envelope.add_scene_view(view)

    def add_camera_view(self, view: CameraView) -> None:
        self._envelope.add_camera_view(view)

    # ── optional purpose files ──────────────────────────────────────────────

    def add_model_property(
        self, path: str, value: Any, unit: str | None = None
    ) -> None:
        """Document-scoped eav row (``eav.model``); ``None`` and non-finite values
        write nothing."""
        if not path or value is None:
            return
        string = double = boolean = None
        if isinstance(value, bool):
            boolean = value
        elif isinstance(value, (int, float)):
            double = float(value)
            if not math.isfinite(double):
                return
        else:
            string = str(value)
        if self._model is None:
            self._model = ModelEavWriter(self.output_dir, self.base_name)
        self._model.add_row(path, string, double, boolean, unit)

    def add_model_placement(
        self,
        default: str,
        transform: Sequence[float],
        units: str | None,
        applied_to_geometry: bool,
        *,
        source: str | None = None,
        options: Mapping[str, Sequence[float]] | None = None,
    ) -> None:
        """Where the model sits: host internal → ``default`` datum, plus every
        selectable datum in ``options``."""
        if options and default not in options:
            raise ValueError(
                f"modelPlacement default '{default}' is not one of {sorted(options)}"
            )
        for kind, t in (options or {}).items():
            self.add_model_property(
                f"modelPlacement.options.{kind}.transform", _format_transform(t)
            )
        self.add_model_property("modelPlacement.default", default)
        self.add_model_property("modelPlacement.source", source or default)
        self.add_model_property(
            "modelPlacement.transform", _format_transform(transform)
        )
        self.add_model_property("modelPlacement.units", units)
        self.add_model_property("modelPlacement.appliedToGeometry", applied_to_geometry)

    def add_property_set_definition(
        self,
        set_name: str,
        set_key: str,
        field_name: str,
        field_bucket_id: str | None = None,
        data_type: str | None = None,
        *,
        default_string: str | None = None,
        default_double: float | None = None,
        default_boolean: bool | None = None,
        unit: str | None = None,
        description: str | None = None,
        set_description: str | None = None,
        applies_to: str | None = None,
    ) -> None:
        """One field of a property-set schema; call in authored field order."""
        if self._property_sets is None:
            self._property_sets = PropertySetDefinitionsWriter(
                self.output_dir, self.base_name
            )
        self._property_sets.add_row(
            set_name,
            set_key,
            set_description,
            field_name,
            field_bucket_id,
            data_type,
            default_string,
            default_double,
            default_boolean,
            unit,
            description,
            applies_to,
        )

    # ── lifecycle ───────────────────────────────────────────────────────────

    def complete(self) -> None:
        self._geometries.complete()
        self._envelope.complete()
        self._eav.complete()
        if self._model is not None:
            self._model.complete()
        if self._property_sets is not None:
            self._property_sets.complete()

    def __enter__(self) -> ObjectsArtifactPipeline:
        return self

    def __exit__(self, *exc: object) -> None:
        self.complete()


def _try_split_type_parameters(
    properties: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Split ``properties.Parameters`` into instance-scoped and type-scoped
    (``Type Parameters`` / ``System Type Parameters``); None if nothing type-scoped."""
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
