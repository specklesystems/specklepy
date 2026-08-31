"""Authoring façade over :class:`ObjectsArtifactPipeline` (port of the .NET
``BundleBuilder``).

``get_or_add_*`` interns a node by key — the same key returns the same handle and writes
nothing; a repeat with different attributes raises. ``add_*`` appends a row every call.
Property setters and verbs emit one edge each, and an edge cannot be retracted.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from specklepy.bundle.envelope_writer import (
    CameraView,
    Producer,
    SceneView,
    SceneViewKey,
)
from specklepy.bundle.pipeline import ObjectsArtifactPipeline
from specklepy.bundle.spec import Rel

DEFAULT_BASE_NAME = "bundle"

T = TypeVar("T")


def _same(key: str, written: T, requested: T, what: str) -> None:
    if written != requested:
        raise ValueError(
            f"Key '{key}' was already added with {what} '{written}'; a second "
            f"get_or_add asked for '{requested}'. One key means one node — use a "
            "different key for different content."
        )


@dataclass(frozen=True)
class BundleFiles:
    directory: str
    base_name: str
    files: list[str]
    object_count: int

    @property
    def by_name(self) -> dict[str, str]:
        return {os.path.basename(p): p for p in self.files}

    def rename_to(self, version_id: str) -> BundleFiles:
        if version_id == self.base_name:
            return self
        renamed = []
        for path in self.files:
            name = os.path.basename(path)
            target = os.path.join(
                self.directory, version_id + name[len(self.base_name) :]
            )
            os.replace(path, target)
            renamed.append(target)
        return BundleFiles(
            self.directory, version_id, sorted(renamed), self.object_count
        )


class BundleBuilder:
    def __init__(
        self,
        producer: Producer,
        units: str,
        output_dir: str | None = None,
        base_name: str = DEFAULT_BASE_NAME,
    ) -> None:
        if not units or not units.strip():
            raise ValueError("units is required")
        self.producer = producer
        self.units = units
        self.directory = output_dir or tempfile.mkdtemp(prefix="speckle-bundle-")
        self.base_name = base_name
        os.makedirs(self.directory, exist_ok=True)
        self.pipeline = ObjectsArtifactPipeline(self.directory, base_name, producer)
        self._objects: dict[str, BundleObject] = {}
        self._containers: dict[str, BundleContainer] = {}
        self._definitions: dict[str, BundleDefinition] = {}
        self._materials: dict[str, BundleMaterial] = {}
        self._colors: dict[int, BundleColor] = {}
        self._levels: dict[str, BundleLevel] = {}
        self._geometries: dict[str, BundleGeometry] = {}
        self._scene_views: list[SceneView] = []
        self._built = False

    @property
    def objects(self) -> list[BundleObject]:
        return list(self._objects.values())

    # ── containers ───────────────────────────────────────────────────────────

    def get_or_add_container_path(
        self,
        path: Sequence[str],
        subtype: str = "Collection",
        gh_topology: str | None = None,
    ) -> BundleContainer:
        if not path:
            raise ValueError("A collection path needs at least one segment.")
        parent: BundleContainer | None = None
        key = ""
        for i, segment in enumerate(path):
            key = segment if not key else f"{key}/{segment}"
            leaf = i == len(path) - 1
            parent = self.get_or_add_container(
                key, segment, parent, subtype, gh_topology if leaf else None
            )
        assert parent is not None
        return parent

    def get_or_add_container(
        self,
        key: str,
        name: str | None,
        parent: BundleContainer | None,
        subtype: str,
        gh_topology: str | None = None,
    ) -> BundleContainer:
        existing = self._containers.get(key)
        if existing is not None:
            _same(key, existing.name, name, "name")
            _same(key, existing.subtype, subtype, "subtype")
            _same(
                key,
                existing.parent.key if existing.parent else None,
                parent.key if parent else None,
                "parent",
            )
            return existing
        k = self.pipeline.add_collection(
            key, name, parent.k if parent else None, subtype, gh_topology=gh_topology
        )
        container = BundleContainer(self, k, key, name, subtype, parent)
        self._containers[key] = container
        return container

    # ── objects ──────────────────────────────────────────────────────────────

    def get_or_add_object(self, application_id: str) -> BundleObject:
        obj = self._objects.get(application_id)
        if obj is None:
            obj = BundleObject(
                self, self.pipeline.intern_object(application_id), application_id
            )
            self._objects[application_id] = obj
        return obj

    def try_get_object(self, application_id: str) -> BundleObject | None:
        return self._objects.get(application_id)

    def try_get_geometry(self, geometry_key: str) -> BundleGeometry | None:
        return self._geometries.get(geometry_key)

    def try_get_definition(self, key: str) -> BundleDefinition | None:
        return self._definitions.get(key)

    def _write_properties(
        self,
        obj: BundleObject,
        properties: Mapping[str, Any] | None,
        name: str | None,
        speckle_type: str | None,
        source_type: str | None,
        units: str | None,
        type_key: str | None,
        root_scalars: Iterable[tuple[str, Any]] | None,
    ) -> None:
        scalars: list[tuple[str, Any]] = [
            ("speckle_type", speckle_type),
            ("name", name),
            ("units", units or self.units),
            ("type", source_type),
        ]
        if root_scalars is not None:
            scalars.extend(root_scalars)
        self.pipeline.add_properties(
            obj.application_id, properties or {}, scalars, type_key
        )

    # ── value nodes ──────────────────────────────────────────────────────────

    def get_or_add_material(
        self,
        key: str,
        name: str | None,
        argb: int,
        opacity: float = 1.0,
        metalness: float = 0.0,
        roughness: float = 1.0,
        emissive: int | None = None,
        ior: float | None = None,
    ) -> BundleMaterial:
        existing = self._materials.get(key)
        if existing is not None:
            _same(key, existing.name, name, "name")
            _same(key, existing.argb, argb, "argb")
            return existing
        k = self.pipeline.add_material(
            key,
            argb,
            opacity,
            metalness,
            roughness,
            name=name,
            emissive=emissive,
            ior=ior,
        )
        material = BundleMaterial(self, k, key, name, argb)
        self._materials[key] = material
        return material

    def get_or_add_color(self, argb: int) -> BundleColor:
        color = self._colors.get(argb)
        if color is None:
            color = BundleColor(self, self.pipeline.add_color(argb), argb)
            self._colors[argb] = color
        return color

    def get_or_add_level(
        self, key: str, name: str | None, elevation: float
    ) -> BundleLevel:
        existing = self._levels.get(key)
        if existing is not None:
            _same(key, existing.name, name, "name")
            _same(key, existing.elevation, elevation, "elevation")
            return existing
        level = BundleLevel(
            self, self.pipeline.add_level(key, name, elevation), key, name, elevation
        )
        self._levels[key] = level
        return level

    def get_or_add_definition(
        self,
        key: str,
        name: str | None,
        populate: Callable[[BundleDefinition], None] | None = None,
    ) -> BundleDefinition:
        existing = self._definitions.get(key)
        if existing is not None:
            if name is not None:
                _same(key, existing.name, name, "name")
            return existing
        definition = BundleDefinition(
            self, self.pipeline.add_definition(key, name), key, name
        )
        self._definitions[key] = definition
        if populate is not None:
            populate(definition)
        return definition

    # ── model-level rows ─────────────────────────────────────────────────────

    def add_model_property(
        self, path: str, value: Any, unit: str | None = None
    ) -> None:
        self.pipeline.add_model_property(path, value, unit)

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
        self.pipeline.add_model_placement(
            default,
            transform,
            units,
            applied_to_geometry,
            source=source,
            options=options,
        )

    def add_property_set_definition(self, *args: Any, **kwargs: Any) -> None:
        self.pipeline.add_property_set_definition(*args, **kwargs)

    def add_camera_view(self, view: CameraView) -> None:
        self.pipeline.add_camera_view(view)

    def scene_view(self, name: str, is_default: bool, *tiers: SceneViewKey) -> None:
        view = SceneView(len(self._scene_views), name, is_default, list(tiers))
        self._scene_views.append(view)
        self.pipeline.add_scene_view(view)

    # ── lifecycle ────────────────────────────────────────────────────────────

    def build(self) -> BundleFiles:
        if self._built:
            raise RuntimeError("build() has already been called on this BundleBuilder.")
        self._built = True
        if not self._scene_views:
            self.scene_view("Default", True, SceneViewKey.rel(Rel.IN_COLLECTION))
        self.pipeline.complete()
        prefix = self.base_name + "."
        files = sorted(
            os.path.join(self.directory, f)
            for f in os.listdir(self.directory)
            if f.startswith(prefix) and f.endswith(".parquet")
        )
        return BundleFiles(self.directory, self.base_name, files, len(self._objects))

    def __enter__(self) -> BundleBuilder:
        return self

    def __exit__(self, *exc: object) -> None:
        if not self._built:
            self.pipeline.complete()


# ── handles ──────────────────────────────────────────────────────────────────


class _BundleNode:
    def __init__(self, builder: BundleBuilder, k: int) -> None:
        self._builder = builder
        self.k = k
        self._material: BundleMaterial | None = None
        self._color: BundleColor | None = None

    # node-plane appearance re-emits on a different value; only object handles guard
    @property
    def material(self) -> BundleMaterial | None:
        return self._material

    @material.setter
    def material(self, value: BundleMaterial | None) -> None:
        if value is not None and value is not self._material:
            self._builder.pipeline.node_has_material(self.k, value.k)
        self._material = value

    @property
    def color(self) -> BundleColor | None:
        return self._color

    @color.setter
    def color(self, value: BundleColor | None) -> None:
        if value is not None and value is not self._color:
            self._builder.pipeline.node_has_color(self.k, value.k)
        self._color = value


class BundleContainer(_BundleNode):
    def __init__(
        self,
        builder: BundleBuilder,
        k: int,
        key: str,
        name: str | None,
        subtype: str,
        parent: BundleContainer | None,
    ) -> None:
        super().__init__(builder, k)
        self.key = key
        self.name = name
        self.subtype = subtype
        self.parent = parent

    def __repr__(self) -> str:
        return f"{self.subtype} '{self.name}'"


class BundleLevel(_BundleNode):
    def __init__(
        self,
        builder: BundleBuilder,
        k: int,
        key: str,
        name: str | None,
        elevation: float,
    ) -> None:
        super().__init__(builder, k)
        self.key = key
        self.name = name
        self.elevation = elevation


class BundleMaterial(_BundleNode):
    def __init__(
        self, builder: BundleBuilder, k: int, key: str, name: str | None, argb: int
    ) -> None:
        super().__init__(builder, k)
        self.key = key
        self.name = name
        self.argb = argb


class BundleColor(_BundleNode):
    def __init__(self, builder: BundleBuilder, k: int, argb: int) -> None:
        super().__init__(builder, k)
        self.argb = argb


class BundleInstance(_BundleNode):
    def __init__(
        self, builder: BundleBuilder, k: int, definition: BundleDefinition
    ) -> None:
        super().__init__(builder, k)
        self.definition = definition


class BundleGeometry:
    def __init__(self, builder: BundleBuilder, k: int, ord: int) -> None:
        self._builder = builder
        self.k = k
        self.ord = ord
        self._material: BundleMaterial | None = None
        self._color: BundleColor | None = None

    @property
    def material(self) -> BundleMaterial | None:
        return self._material

    @material.setter
    def material(self, value: BundleMaterial | None) -> None:
        if value is not None and value is not self._material:
            self._builder.pipeline.has_material(self.k, value.k)
        self._material = value

    @property
    def color(self) -> BundleColor | None:
        return self._color

    @color.setter
    def color(self, value: BundleColor | None) -> None:
        if value is not None and value is not self._color:
            self._builder.pipeline.has_color(self.k, value.k)
        self._color = value


class BundleDefinition(_BundleNode):
    """DEFINES / DEFINES_INSTANCE / DEFINES_MEMBER share one member-ordinal space; the
    (definition, ordinal) pair is what joins a member's object row to its geometry."""

    def __init__(
        self, builder: BundleBuilder, k: int, key: str, name: str | None
    ) -> None:
        super().__init__(builder, k)
        self.key = key
        self.name = name
        self._geometry_ord = 0
        self._member_ord = 0

    def _next_member_ordinal(self) -> int:
        return max(self._geometry_ord, self._member_ord)

    def _bump(self, ord: int) -> None:
        self._geometry_ord = max(self._geometry_ord, ord + 1)
        self._member_ord = max(self._member_ord, ord + 1)

    def add_geometry(
        self,
        geometry: Any,
        geometry_key: str | None = None,
        member_ord: int | None = None,
    ) -> BundleGeometry:
        ord = member_ord if member_ord is not None else self._take_geometry_ord()
        k = self._builder.pipeline.add_geometry(
            geometry_key or f"{self.key}:g{ord}", geometry
        )
        self._builder.pipeline.defines(self.k, k, ord)
        return BundleGeometry(self._builder, k, ord)

    def add_raw_geometry(
        self,
        content: bytes,
        type: str,
        geometry_key: str | None = None,
        member_ord: int | None = None,
    ) -> BundleGeometry:
        ord = member_ord if member_ord is not None else self._take_geometry_ord()
        k = self._builder.pipeline.add_raw_geometry(
            geometry_key or f"{self.key}:raw{ord}", content, type
        )
        self._builder.pipeline.defines(self.k, k, ord)
        return BundleGeometry(self._builder, k, ord)

    def place_nested(
        self,
        definition: BundleDefinition,
        transform: Sequence[float],
        units: str | None = None,
        key: str | None = None,
    ) -> BundleInstance:
        ord = self._take_geometry_ord()
        k = self._builder.pipeline.add_instance(
            key or f"{self.key}:inst{ord}", definition.k, transform, units
        )
        self._builder.pipeline.defines_instance(self.k, k, ord)
        return BundleInstance(self._builder, k, definition)

    def add_member(
        self,
        member: BundleObject,
        geometry: Iterable[Any],
        member_ord: int | None = None,
    ) -> list[BundleGeometry]:
        ord = member_ord if member_ord is not None else self._next_member_ordinal()
        self._bump(ord)
        pipeline = self._builder.pipeline
        pipeline.defines_member(self.k, member.k, ord)
        result: list[BundleGeometry] = []
        for i, g in enumerate(geometry):
            key = f"{member.application_id}:g{i}"
            k = pipeline.add_geometry(key, g)
            pipeline.defines(self.k, k, ord)
            handle = BundleGeometry(self._builder, k, ord)
            self._builder._geometries[key] = handle
            result.append(handle)
        return result

    def add_member_raw_geometry(
        self, member: BundleObject, content: bytes, type: str, member_ord: int
    ) -> BundleGeometry:
        key = f"{member.application_id}:raw{member_ord}"
        k = self._builder.pipeline.add_raw_geometry(key, content, type)
        self._builder.pipeline.defines(self.k, k, member_ord)
        handle = BundleGeometry(self._builder, k, member_ord)
        self._builder._geometries[key] = handle
        return handle

    def add_member_placement(
        self,
        member: BundleObject,
        nested: BundleDefinition,
        transform: Sequence[float],
        units: str | None = None,
        member_ord: int | None = None,
    ) -> BundleInstance:
        ord = member_ord if member_ord is not None else self._next_member_ordinal()
        self._bump(ord)
        pipeline = self._builder.pipeline
        k = pipeline.add_instance(
            member.application_id, nested.k, transform, units or self._builder.units
        )
        pipeline.defines_instance(self.k, k, ord)
        pipeline.defines_member(self.k, member.k, ord)
        pipeline.places(member.k, k)
        return BundleInstance(self._builder, k, nested)

    def add_existing_geometry(
        self, geometry: BundleGeometry, member_ord: int | None = None
    ) -> None:
        ord = member_ord if member_ord is not None else self._next_member_ordinal()
        self._bump(ord)
        self._builder.pipeline.defines(self.k, geometry.k, ord)

    def _take_geometry_ord(self) -> int:
        ord = self._geometry_ord
        self._geometry_ord += 1
        return ord


class BundleObject:
    def __init__(self, builder: BundleBuilder, k: int, application_id: str) -> None:
        self._builder = builder
        self.k = k
        self.application_id = application_id
        self.name: str | None = None
        self.properties_written = False
        self.geometries: list[BundleGeometry] = []
        self.assembly: BundleObject | None = None
        self._parent: BundleObject | None = None
        self._collection: BundleContainer | None = None
        self._model: BundleContainer | None = None
        self._system: BundleContainer | None = None
        self._level: BundleLevel | None = None
        self._material: BundleMaterial | None = None
        self._color: BundleColor | None = None
        self._host: BundleObject | None = None
        self._room: BundleObject | None = None
        self._display_ord = 0
        self._solid_ord = 0
        self._placement_ord = 0
        self._child_ord = 0

    def __repr__(self) -> str:
        return (
            self.application_id
            if self.name is None
            else f"{self.name} ({self.application_id})"
        )

    # ── properties ───────────────────────────────────────────────────────────

    def set_properties(
        self,
        properties: Mapping[str, Any] | None = None,
        *,
        name: str | None = None,
        speckle_type: str | None = None,
        source_type: str | None = None,
        units: str | None = None,
        type_key: str | None = None,
        root_scalars: Iterable[tuple[str, Any]] | None = None,
    ) -> BundleObject:
        if self.properties_written:
            raise RuntimeError(
                f"Properties for '{self.application_id}' were already written; an "
                "object's properties are written once."
            )
        self._builder._write_properties(
            self,
            properties,
            name,
            speckle_type,
            source_type,
            units,
            type_key,
            root_scalars,
        )
        self.properties_written = True
        self.name = name
        return self

    # ── geometry ─────────────────────────────────────────────────────────────

    def add_geometry(
        self, geometry: Any, geometry_key: str | None = None
    ) -> BundleGeometry:
        ord = self._display_ord
        self._display_ord += 1
        key = geometry_key or f"{self.application_id}:g{ord}"
        k = self._builder.pipeline.add_geometry(key, geometry)
        self._builder.pipeline.display(self.k, k, ord)
        return self._register(key, BundleGeometry(self._builder, k, ord))

    def add_raw_geometry(
        self, content: bytes, type: str, geometry_key: str | None = None
    ) -> BundleGeometry:
        ord = self._solid_ord
        self._solid_ord += 1
        key = geometry_key or f"{self.application_id}:raw{ord}"
        k = self._builder.pipeline.add_raw_geometry(key, content, type)
        self._builder.pipeline.solid(self.k, k, ord)
        return self._register(key, BundleGeometry(self._builder, k, ord))

    def _register(self, key: str, geometry: BundleGeometry) -> BundleGeometry:
        self._builder._geometries[key] = geometry
        self.geometries.append(geometry)
        return geometry

    def place(
        self,
        definition: BundleDefinition,
        transform: Sequence[float],
        units: str | None = None,
        key: str | None = None,
    ) -> BundleInstance:
        ord = self._placement_ord
        self._placement_ord += 1
        k = self._builder.pipeline.add_instance(
            key or f"{self.application_id}:inst{ord}",
            definition.k,
            transform,
            units or self._builder.units,
        )
        self._builder.pipeline.display_instance(self.k, k, ord)
        return BundleInstance(self._builder, k, definition)

    # ── single-valued relations (one edge, never retracted) ──────────────────

    def _set(self, attr: str, value: Any, emit: Callable[[int], None]) -> None:
        current = getattr(self, attr)
        if current is value:
            return
        if current is not None:
            raise RuntimeError(
                "This relation was already set; a bundle edge cannot be retracted."
            )
        if value is None:
            return
        setattr(self, attr, value)
        emit(value.k)

    @property
    def collection(self) -> BundleContainer | None:
        return self._collection

    @collection.setter
    def collection(self, value: BundleContainer | None) -> None:
        self._set(
            "_collection",
            value,
            lambda k: self._builder.pipeline.in_collection(self.k, k, 0),
        )

    @property
    def model(self) -> BundleContainer | None:
        return self._model

    @model.setter
    def model(self, value: BundleContainer | None) -> None:
        self._set(
            "_model", value, lambda k: self._builder.pipeline.in_model(self.k, k, 0)
        )

    @property
    def system(self) -> BundleContainer | None:
        return self._system

    @system.setter
    def system(self, value: BundleContainer | None) -> None:
        self._set(
            "_system", value, lambda k: self._builder.pipeline.in_system(self.k, k, 0)
        )

    @property
    def level(self) -> BundleLevel | None:
        return self._level

    @level.setter
    def level(self, value: BundleLevel | None) -> None:
        self._set("_level", value, lambda k: self._builder.pipeline.on_level(self.k, k))

    @property
    def material(self) -> BundleMaterial | None:
        return self._material

    @material.setter
    def material(self, value: BundleMaterial | None) -> None:
        self._set(
            "_material",
            value,
            lambda k: self._builder.pipeline.object_has_material(self.k, k),
        )

    @property
    def color(self) -> BundleColor | None:
        return self._color

    @color.setter
    def color(self, value: BundleColor | None) -> None:
        self._set(
            "_color",
            value,
            lambda k: self._builder.pipeline.object_has_color(self.k, k),
        )

    @property
    def host(self) -> BundleObject | None:
        return self._host

    @host.setter
    def host(self, value: BundleObject | None) -> None:
        self._set("_host", value, lambda k: self._builder.pipeline.hosted_on(self.k, k))

    @property
    def room(self) -> BundleObject | None:
        return self._room

    @room.setter
    def room(self, value: BundleObject | None) -> None:
        self._set(
            "_room", value, lambda k: self._builder.pipeline.in_room(self.k, k, 0)
        )

    @property
    def parent(self) -> BundleObject | None:
        return self._parent

    @parent.setter
    def parent(self, value: BundleObject | None) -> None:
        if value is not None:
            value.add_child(self)

    # ── multi-valued relations ───────────────────────────────────────────────

    def add_child(self, child: BundleObject, ord: int | None = None) -> None:
        if child._parent is self:
            return
        if child._parent is not None:
            raise RuntimeError(
                f"Object '{child.application_id}' already has parent "
                f"'{child._parent.application_id}'; a bundle edge cannot be retracted"
            )
        o = self._child_ord if ord is None else ord
        self._child_ord = max(self._child_ord, o + 1)
        child._parent = self
        self._builder.pipeline.subelement(self.k, child.k, o)

    def add_assembly_member(self, member: BundleObject, ord: int | None = None) -> None:
        if member.assembly is self:
            return
        if member.assembly is not None:
            raise RuntimeError(
                f"Object '{member.application_id}' is already in assembly "
                f"'{member.assembly.application_id}'; a bundle edge cannot be "
                "retracted."
            )
        o = self._assembly_member_ord if ord is None else ord
        self._assembly_member_ord = max(self._assembly_member_ord, o + 1)
        member.assembly = self
        self._builder.pipeline.in_assembly(member.k, self.k, o)

    _assembly_member_ord = 0

    def add_to_group(self, group: BundleContainer, ord: int = 0) -> None:
        self._builder.pipeline.in_group(self.k, group.k, ord)

    def connect_to(self, other: BundleObject, scope: int = 0) -> None:
        self._builder.pipeline.connects_to(self.k, other.k, scope)

    def bounds(self, room: BundleObject, ord: int = 0) -> None:
        self._builder.pipeline.bounds(self.k, room.k, ord)
