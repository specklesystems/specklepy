"""Read façade over a received bundle (port of .NET ``Speckle.Sdk.Bundles.Model``)."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, TypeVar

from specklepy.bundle import sgeo
from specklepy.bundle.bundle_reader import (
    ArtefactBundle,
    Geometry,
    Node,
    read_geometries,
)
from specklepy.bundle.envelope_writer import CameraView
from specklepy.bundle.property_table import PropertyView
from specklepy.bundle.spec import NodeKind, Rel

if TYPE_CHECKING:
    from specklepy.objects.base import Base
    from specklepy.objects.models.collections.collection import Collection

log = logging.getLogger(__name__)

PROPERTIES_ROOT = "properties"
PROPERTIES_PREFIX = "properties."
NESTING_GUARD = 32
ANCESTRY_GUARD = 64

Transform = Sequence[float]


class GeometryRole(Enum):
    DISPLAY = "display"
    SOLID = "solid"


@dataclass(frozen=True)
class SceneViewTier:
    source: str
    ref: str

    @property
    def is_relation(self) -> bool:
        return self.source == "rel"

    @property
    def relation(self) -> int | None:
        return int(self.ref) if self.is_relation and self.ref.isdigit() else None

    @property
    def property_path(self) -> str | None:
        return self.ref if self.source == "eav" else None


@dataclass(frozen=True)
class SceneViewSegment:
    name: str
    node: ModelNode | None


class Model:
    """A received version. Owns its download directory until :meth:`close`; parsed
    data stays usable afterwards, geometry is parsed from disk on first access."""

    def __init__(
        self,
        project_id: str,
        model_id: str,
        version_id: str,
        directory: str,
        files: Sequence[str],
        bundle: ArtefactBundle,
        geometry_downloaded: bool = True,
    ) -> None:
        self.project_id = project_id
        self.model_id = model_id
        self.version_id = version_id
        self.directory = directory
        self.files = list(files)
        self.bundle = bundle
        self._geometry_downloaded = geometry_downloaded
        self._closed = False
        if bundle.relations.unknown_rels:
            log.warning(
                "bundle %s/%s/%s uses relation ids this SDK does not know: %s",
                project_id,
                model_id,
                version_id,
                sorted(bundle.relations.unknown_rels),
            )

    # ── lifecycle ────────────────────────────────────────────────────────────

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        shutil.rmtree(self.directory, ignore_errors=True)

    def __enter__(self) -> Model:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ── model-level ──────────────────────────────────────────────────────────

    @property
    def units(self) -> str:
        return self.bundle.units

    @property
    def properties(self) -> dict[str, object]:
        return self.bundle.model_properties

    @cached_property
    def default_scene_view(self) -> list[SceneViewTier]:
        return [SceneViewTier(t.source, t.ref) for t in self.bundle.default_scene_view]

    @property
    def camera_views(self) -> list[CameraView]:
        return self.bundle.camera_views

    @property
    def property_set_definitions(self):
        return self.bundle.property_set_definitions

    @property
    def unknown_relations(self) -> set[int]:
        return self.bundle.relations.unknown_rels

    @cached_property
    def property_paths(self) -> list[str]:
        return [
            p[len(PROPERTIES_PREFIX) :]
            for p in self.bundle.property_table.paths
            if p.startswith(PROPERTIES_PREFIX)
        ]

    def objects_with(self, path: str) -> list[ModelObject]:
        keys = self.bundle.property_table.keys_with(PROPERTIES_PREFIX + path)
        return [o for k in keys if (o := self.object(k)) is not None]

    # ── objects ──────────────────────────────────────────────────────────────

    @cached_property
    def objects(self) -> list[ModelObject]:
        return [
            ModelObject(self, k, app_id)
            for k, app_id in sorted(self.bundle.object_app_ids.items())
        ]

    @cached_property
    def _objects_by_k(self) -> dict[int, ModelObject]:
        return {o.k: o for o in self.objects}

    @cached_property
    def _objects_by_app_id(self) -> dict[str, ModelObject]:
        return {o.application_id: o for o in self.objects}

    def object(self, k: int) -> ModelObject | None:
        return self._objects_by_k.get(k)

    def object_by_application_id(self, application_id: str) -> ModelObject | None:
        return self._objects_by_app_id.get(application_id)

    # ── nodes ────────────────────────────────────────────────────────────────

    @cached_property
    def nodes(self) -> dict[int, ModelNode]:
        return {k: _make_node(self, k, n) for k, n in self.bundle.nodes.items()}

    def node(self, k: int | None) -> ModelNode | None:
        return None if k is None else self.nodes.get(k)

    def _nodes_of(self, cls: type[N]) -> list[N]:
        return [n for _, n in sorted(self.nodes.items()) if isinstance(n, cls)]

    @cached_property
    def levels(self) -> list[ModelLevel]:
        return self._nodes_of(ModelLevel)

    @cached_property
    def materials(self) -> list[ModelMaterial]:
        return self._nodes_of(ModelMaterial)

    @cached_property
    def colors(self) -> list[ModelColor]:
        return self._nodes_of(ModelColor)

    @cached_property
    def definitions(self) -> list[ModelDefinition]:
        return self._nodes_of(ModelDefinition)

    @cached_property
    def collections(self) -> list[ModelContainer]:
        return self._nodes_of(ModelContainer)

    # ── geometry ─────────────────────────────────────────────────────────────

    @property
    def is_geometry_loaded(self) -> bool:
        return "geometries" in self.__dict__

    @cached_property
    def geometries(self) -> dict[int, Geometry]:
        if self.bundle.geometries:
            return self.bundle.geometries
        if not self._geometry_downloaded:
            raise RuntimeError(
                "This model was received with include_geometry=False; receive it "
                "again to access geometry."
            )
        if self._closed:
            raise RuntimeError(
                "Geometry is parsed from the bundle files on first access and this "
                "model has been closed; access Model.geometries before closing."
            )
        return read_geometries(self.directory)

    # ── projection ───────────────────────────────────────────────────────────

    def to_base(self) -> Collection:
        from specklepy.bundle.base_projection import to_base

        return to_base(self)

    # ── indexes ──────────────────────────────────────────────────────────────

    @cached_property
    def index(self) -> RelationIndex:
        return RelationIndex(self.bundle)

    def _objects_for(self, ks: Sequence[int] | None) -> list[ModelObject]:
        if not ks:
            return []
        return [o for k in ks if (o := self.object(k)) is not None]

    def _nodes_for(self, cls: type[N], ks: Sequence[int] | None) -> list[N]:
        if not ks:
            return []
        return [n for k in ks if isinstance(n := self.node(k), cls)]


class RelationIndex:
    def __init__(self, bundle: ArtefactBundle) -> None:
        r = bundle.relations
        self.children_by_parent: dict[int, list[int]] = {}
        self.parent_by_child: dict[int, int] = {}
        self.hosted_by_host: dict[int, list[int]] = {}
        self.host_by_hosted: dict[int, int] = {}
        self.connections: dict[int, list[int]] = {}
        self.rooms_by_bounding: dict[int, list[int]] = {}
        self.bounding_by_room: dict[int, list[int]] = {}
        self.room_by_object: dict[int, int] = {}
        self.objects_by_room: dict[int, list[int]] = {}
        self.assembly_by_member: dict[int, int] = {}
        self.members_by_assembly: dict[int, list[int]] = {}
        self.instances_by_object: dict[int, list[int]] = {}
        self.instances_by_definition: dict[int, list[int]] = {}
        self.objects_by_definition: dict[int, list[int]] = {}
        self.objects_by_collection: dict[int, list[int]] = {}
        self.objects_by_level: dict[int, list[int]] = {}
        self.child_containers_by_container: dict[int, list[int]] = {}

        for e in sorted(r.subelement, key=lambda e: e.ord):
            _add(self.children_by_parent, e.src, e.dst)
            self.parent_by_child[e.dst] = e.src
        for e in r.hosted_on:
            _add(self.hosted_by_host, e.dst, e.src)
            self.host_by_hosted[e.src] = e.dst
        for e in r.connects_to:
            _add(self.connections, e.src, e.dst)
            _add(self.connections, e.dst, e.src)
        for e in sorted(r.bounds, key=lambda e: e.ord):
            _add(self.rooms_by_bounding, e.src, e.dst)
            _add(self.bounding_by_room, e.dst, e.src)
        for e in r.in_room:
            self.room_by_object[e.src] = e.dst
            _add(self.objects_by_room, e.dst, e.src)
        for e in sorted(r.in_assembly, key=lambda e: e.ord):
            self.assembly_by_member[e.src] = e.dst
            _add(self.members_by_assembly, e.dst, e.src)
        for e in sorted(r.display_instance_edges, key=lambda e: e.ord):
            _add(self.instances_by_object, e.src, e.dst)
            inst = bundle.nodes.get(e.dst)
            if inst is not None and inst.def_ref is not None:
                objs = self.objects_by_definition.setdefault(inst.def_ref, [])
                if e.src not in objs:
                    objs.append(e.src)
        for k, n in bundle.nodes.items():
            if n.def_ref is None:
                continue
            if n.kind == NodeKind.INSTANCE:
                _add(self.instances_by_definition, n.def_ref, k)
            elif n.kind == NodeKind.CONTAINER:
                _add(self.child_containers_by_container, n.def_ref, k)
        for obj, level in r.object_node_by_rel.get(int(Rel.ON_LEVEL), {}).items():
            _add(self.objects_by_level, level, obj)
        for obj, coll in r.collection_by_object.items():
            _add(self.objects_by_collection, coll, obj)


def _add(index: dict[int, list[int]], key: int, value: int) -> None:
    index.setdefault(key, []).append(value)


class ModelObject:
    def __init__(self, model: Model, k: int, application_id: str) -> None:
        self._model = model
        self.k = k
        self.application_id = application_id

    def __repr__(self) -> str:
        name = self.name
        return (
            self.application_id if name is None else f"{name} ({self.application_id})"
        )

    @property
    def _type_k(self) -> int | None:
        return self._model.bundle.type_index_by_object.get(self.k)

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def name(self) -> str | None:
        return self._model.bundle.property_table.get_string(self.k, "name")

    @property
    def properties(self) -> PropertyView:
        return self._model.bundle.property_table.under(self.k, PROPERTIES_ROOT)

    @property
    def root_properties(self) -> PropertyView:
        return self._model.bundle.property_table.view(self.k)

    @property
    def type_properties(self) -> PropertyView:
        return self._model.bundle.type_properties(self.k).under(PROPERTIES_ROOT)

    def __getitem__(self, path: str) -> object | None:
        table = self._model.bundle.property_table
        found, value = table.try_get(self.k, PROPERTIES_PREFIX + path)
        if found:
            return value
        type_k = self._type_k
        if type_k is not None:
            found, value = self._model.bundle.type_property_table.try_get(
                type_k, PROPERTIES_PREFIX + path
            )
            if found:
                return value
        return table.try_get(self.k, path)[1]

    def _typed(self, getter: str, path: str):
        table = self._model.bundle.property_table
        value = getattr(table, getter)(self.k, PROPERTIES_PREFIX + path)
        if value is None and self._type_k is not None:
            value = getattr(self._model.bundle.type_property_table, getter)(
                self._type_k, PROPERTIES_PREFIX + path
            )
        if value is None:
            value = getattr(table, getter)(self.k, path)
        return value

    def get_double(self, path: str) -> float | None:
        return self._typed("get_double", path)

    def get_string(self, path: str) -> str | None:
        return self._typed("get_string", path)

    def get_bool(self, path: str) -> bool | None:
        return self._typed("get_bool", path)

    # ── geometry ─────────────────────────────────────────────────────────────

    @cached_property
    def geometries(self) -> list[ModelGeometry]:
        model = self._model
        rels = model.bundle.relations
        placements = model.index.instances_by_object.get(self.k)
        has_direct = (
            bool(rels.display_by_object(self.k)) or self.k in rels.solid_by_object
        )
        if not has_direct and not placements:
            return []

        geometries = model.geometries
        result: list[ModelGeometry] = []
        for e in rels.display_by_object(self.k):
            g = geometries.get(e.dst)
            if g is not None:
                result.append(
                    ModelGeometry(model, self, e.dst, g, GeometryRole.DISPLAY, e.ord)
                )
        for i, solid_k in enumerate(rels.solid_by_object.get(self.k, [])):
            g = geometries.get(solid_k)
            if g is not None:
                result.append(
                    ModelGeometry(model, self, solid_k, g, GeometryRole.SOLID, i)
                )
        if placements:
            for e in rels.display_instance_edges:
                if e.src == self.k:
                    self._add_placement(e.dst, e.ord, None, result, 0)
        result.sort(key=lambda g: g.ord)
        return result

    def _add_placement(
        self,
        instance_k: int,
        ord: int,
        parent: Transform | None,
        into: list[ModelGeometry],
        depth: int,
    ) -> None:
        model = self._model
        instance = model.bundle.nodes.get(instance_k)
        if depth > NESTING_GUARD or instance is None or instance.def_ref is None:
            return
        transform = _compose(parent, parse_transform(instance.transform))
        rels = model.bundle.relations
        definition_k = instance.def_ref
        ords = rels.defines_ord_by_definition.get(definition_k)
        for i, geometry_k in enumerate(
            rels.defines_by_definition.get(definition_k, [])
        ):
            g = model.geometries.get(geometry_k)
            if g is not None:
                into.append(
                    ModelGeometry(
                        model,
                        self,
                        geometry_k,
                        g,
                        GeometryRole.DISPLAY,
                        ords[i] if ords else ord,
                        transform,
                        instance_k,
                    )
                )
        for nested_k in rels.defines_instance_by_definition.get(definition_k, []):
            self._add_placement(nested_k, ord, transform, into, depth + 1)

    # ── object → object ──────────────────────────────────────────────────────

    @property
    def parent(self) -> ModelObject | None:
        return self._model.object(self._model.index.parent_by_child.get(self.k, -1))

    @property
    def children(self) -> list[ModelObject]:
        return self._model._objects_for(
            self._model.index.children_by_parent.get(self.k)
        )

    @property
    def host(self) -> ModelObject | None:
        return self._model.object(self._model.index.host_by_hosted.get(self.k, -1))

    @property
    def hosted(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.hosted_by_host.get(self.k))

    @property
    def connected_to(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.connections.get(self.k))

    @property
    def bounds_rooms(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.rooms_by_bounding.get(self.k))

    @property
    def bounded_by(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.bounding_by_room.get(self.k))

    @property
    def room(self) -> ModelObject | None:
        return self._model.object(self._model.index.room_by_object.get(self.k, -1))

    @property
    def contains(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.objects_by_room.get(self.k))

    @property
    def assembly(self) -> ModelObject | None:
        return self._model.object(self._model.index.assembly_by_member.get(self.k, -1))

    @property
    def assembly_members(self) -> list[ModelObject]:
        return self._model._objects_for(
            self._model.index.members_by_assembly.get(self.k)
        )

    # ── object → node ────────────────────────────────────────────────────────

    def _node_by_rel(self, rel: Rel) -> ModelNode | None:
        by_rel = self._model.bundle.relations.object_node_by_rel.get(int(rel), {})
        return self._model.node(by_rel.get(self.k))

    @property
    def level(self) -> ModelLevel | None:
        node = self._node_by_rel(Rel.ON_LEVEL)
        return node if isinstance(node, ModelLevel) else None

    @property
    def system(self) -> ModelContainer | None:
        node = self._node_by_rel(Rel.IN_SYSTEM)
        return node if isinstance(node, ModelContainer) else None

    @property
    def collection(self) -> ModelContainer | None:
        node = self._model.node(
            self._model.bundle.relations.collection_by_object.get(self.k)
        )
        return node if isinstance(node, ModelContainer) else None

    @property
    def groups(self) -> list[ModelContainer]:
        return self._model._nodes_for(
            ModelContainer, self._model.bundle.relations.groups_by_object.get(self.k)
        )

    @cached_property
    def collection_path(self) -> list[str]:
        segments = [name for name, _, _ in _segments(self._model.bundle, self.k)]
        collection_k = self._model.bundle.relations.collection_by_object.get(self.k)
        if segments or collection_k is None:
            return segments
        return _node_ancestry(self._model.bundle.nodes, collection_k)

    @property
    def scene_view_segments(self) -> list[SceneViewSegment]:
        if self._model.bundle.default_scene_view:
            return [
                SceneViewSegment(name, self._model.node(node_k))
                for name, _, node_k in _segments(self._model.bundle, self.k)
            ]
        segments: list[SceneViewSegment] = []
        container = self.collection
        while container is not None:
            segments.insert(0, SceneViewSegment(container.name or "", container))
            container = container.parent
        return segments

    # ── appearance ───────────────────────────────────────────────────────────

    @property
    def material(self) -> ModelMaterial | None:
        node = self._model.node(
            self._model.bundle.relations.material_by_object.get(self.k)
        )
        return node if isinstance(node, ModelMaterial) else None

    @property
    def color(self) -> ModelColor | None:
        node = self._model.node(
            self._model.bundle.relations.color_by_object.get(self.k)
        )
        return node if isinstance(node, ModelColor) else None

    @property
    def container_material(self) -> ModelMaterial | None:
        container = self.collection
        while container is not None:
            if container.material is not None:
                return container.material
            container = container.parent
        return None

    @property
    def container_color(self) -> ModelColor | None:
        container = self.collection
        while container is not None:
            if container.color is not None:
                return container.color
            container = container.parent
        return None

    # ── instancing ───────────────────────────────────────────────────────────

    @property
    def placements(self) -> list[ModelInstance]:
        direct = self._model.index.instances_by_object.get(self.k)
        if direct:
            return self._model._nodes_for(ModelInstance, direct)
        placed = self._model.bundle.relations.places_by_object.get(self.k)
        return self._model._nodes_for(
            ModelInstance, [placed] if placed is not None else None
        )

    @property
    def definitions(self) -> list[ModelDefinition]:
        result: list[ModelDefinition] = []
        for placement in self.placements:
            definition = placement.definition
            if definition is not None and definition not in result:
                result.append(definition)
        return result

    @property
    def definition(self) -> ModelDefinition | None:
        definitions = self.definitions
        return definitions[0] if definitions else None


class ModelGeometry:
    def __init__(
        self,
        model: Model,
        owner: ModelObject,
        k: int,
        geometry: Geometry,
        role: GeometryRole,
        ord: int,
        transform: Transform | None = None,
        instance_k: int | None = None,
    ) -> None:
        self._model = model
        self.owner = owner
        self.k = k
        self.content = geometry.content
        self.type = geometry.type
        self.is_sgeo = geometry.is_sgeo
        self.role = role
        self.ord = ord
        self.transform = None if transform is None else list(transform)
        self._instance_k = instance_k

    @property
    def placement(self) -> ModelInstance | None:
        node = self._model.node(self._instance_k)
        return node if isinstance(node, ModelInstance) else None

    @property
    def material(self) -> ModelMaterial | None:
        node = self._model.node(
            self._model.bundle.relations.material_by_geometry.get(self.k)
        )
        return node if isinstance(node, ModelMaterial) else None

    @property
    def color(self) -> ModelColor | None:
        node = self._model.node(
            self._model.bundle.relations.color_by_geometry.get(self.k)
        )
        return node if isinstance(node, ModelColor) else None

    @property
    def effective_material(self) -> ModelMaterial | None:
        return self.material or self.owner.material or self.owner.container_material

    @property
    def effective_color(self) -> ModelColor | None:
        return self.owner.color or self.color or self.owner.container_color

    def decode(self) -> Base:
        return sgeo.decode(self.content)

    def decode_mesh(self) -> sgeo.DecodedMesh:
        return sgeo.decode_mesh(self.content)


class ModelNode:
    def __init__(self, model: Model, k: int, node: Node) -> None:
        self._model = model
        self._node = node
        self.k = k

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.k}, {self.name!r})"

    @property
    def kind(self) -> int:
        return self._node.kind

    @property
    def name(self) -> str | None:
        return self._node.name

    @property
    def units(self) -> str | None:
        return self._node.units

    @property
    def material(self) -> ModelMaterial | None:
        node = self._model.node(
            self._model.bundle.relations.material_by_node.get(self.k)
        )
        return node if isinstance(node, ModelMaterial) else None

    @property
    def color(self) -> ModelColor | None:
        node = self._model.node(self._model.bundle.relations.color_by_node.get(self.k))
        return node if isinstance(node, ModelColor) else None


class ModelLevel(ModelNode):
    @property
    def elevation(self) -> float | None:
        return self._node.elevation

    @property
    def objects(self) -> list[ModelObject]:
        return self._model._objects_for(self._model.index.objects_by_level.get(self.k))


class ModelMaterial(ModelNode):
    @property
    def argb(self) -> int | None:
        return self._node.argb

    @property
    def opacity(self) -> float | None:
        return self._node.opacity

    @property
    def metalness(self) -> float | None:
        return self._node.metalness

    @property
    def roughness(self) -> float | None:
        return self._node.roughness

    @property
    def emissive(self) -> int | None:
        return self._node.emissive

    @property
    def ior(self) -> float | None:
        return self._node.ior


class ModelColor(ModelNode):
    @property
    def argb(self) -> int:
        return self._node.argb or 0


class ModelDefinition(ModelNode):
    @property
    def placements(self) -> list[ModelInstance]:
        return self._model._nodes_for(
            ModelInstance, self._model.index.instances_by_definition.get(self.k)
        )

    @property
    def members(self) -> list[ModelObject]:
        return self._model._objects_for(
            self._model.bundle.relations.member_objects_by_definition.get(self.k)
        )

    @property
    def objects(self) -> list[ModelObject]:
        return self._model._objects_for(
            self._model.index.objects_by_definition.get(self.k)
        )


class ModelInstance(ModelNode):
    @cached_property
    def transform(self) -> list[float] | None:
        return parse_transform(self._node.transform)

    @property
    def definition(self) -> ModelDefinition | None:
        node = self._model.node(self._node.def_ref)
        return node if isinstance(node, ModelDefinition) else None


class ModelContainer(ModelNode):
    @property
    def subtype(self) -> str | None:
        return self._node.subtype

    @property
    def gh_topology(self) -> str | None:
        return self._node.gh_topology

    @property
    def parent(self) -> ModelContainer | None:
        node = self._model.node(self._node.def_ref)
        return node if isinstance(node, ModelContainer) else None

    @property
    def path(self) -> list[str]:
        return _node_ancestry(self._model.bundle.nodes, self.k)

    @property
    def objects(self) -> list[ModelObject]:
        return self._model._objects_for(
            self._model.index.objects_by_collection.get(self.k)
        )

    @property
    def children(self) -> list[ModelContainer]:
        return self._model._nodes_for(
            ModelContainer, self._model.index.child_containers_by_container.get(self.k)
        )

    @property
    def argb(self) -> int | None:
        return self._node.argb


N = TypeVar("N", bound=ModelNode)

_NODE_TYPES: dict[int, type[ModelNode]] = {
    int(NodeKind.LEVEL): ModelLevel,
    int(NodeKind.MATERIAL): ModelMaterial,
    int(NodeKind.COLOR): ModelColor,
    int(NodeKind.DEFINITION): ModelDefinition,
    int(NodeKind.INSTANCE): ModelInstance,
    int(NodeKind.CONTAINER): ModelContainer,
}


def _make_node(model: Model, k: int, node: Node) -> ModelNode:
    return _NODE_TYPES.get(node.kind, ModelNode)(model, k, node)


def parse_transform(csv: str | None) -> list[float] | None:
    if not csv:
        return None
    parts = csv.split(",")
    if len(parts) != 16:
        return None
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def _compose(parent: Transform | None, child: Transform | None) -> list[float] | None:
    if parent is None:
        return None if child is None else list(child)
    if child is None:
        return list(parent)
    return [
        sum(parent[row * 4 + i] * child[i * 4 + col] for i in range(4))
        for row in range(4)
        for col in range(4)
    ]


# ── scene view resolution ────────────────────────────────────────────────────


def _node_ancestry(nodes: dict[int, Node], node_k: int) -> list[str]:
    return [name for name, _, _ in _node_ancestry_with_appearance(None, nodes, node_k)]


def _node_ancestry_with_appearance(
    bundle: ArtefactBundle | None, nodes: dict[int, Node], node_k: int
) -> list[tuple[str, int | None, int | None]]:
    result: list[tuple[str, int | None, int | None]] = []
    cursor: int | None = node_k
    guard = 0
    while cursor is not None and cursor in nodes and guard < ANCESTRY_GUARD:
        guard += 1
        n = nodes[cursor]
        argb = n.argb
        if bundle is not None:
            color_k = bundle.relations.color_by_node.get(cursor)
            color = nodes.get(color_k) if color_k is not None else None
            if color is not None and color.kind == NodeKind.COLOR:
                argb = color.argb
        result.insert(0, (n.name or "unnamed", argb, cursor))
        cursor = n.def_ref
    return result


def _segments(
    bundle: ArtefactBundle, object_k: int
) -> list[tuple[str, int | None, int | None]]:
    segments: list[tuple[str, int | None, int | None]] = []
    for tier in bundle.default_scene_view:
        if tier.source == "rel":
            if not tier.ref.isdigit():
                continue
            node_k = bundle.relations.object_node_by_rel.get(int(tier.ref), {}).get(
                object_k
            )
            if node_k is not None:
                segments.extend(
                    _node_ancestry_with_appearance(bundle, bundle.nodes, node_k)
                )
        elif tier.source == "eav":
            found, value = bundle.property_table.try_get(object_k, tier.ref)
            if found and value is not None and str(value):
                segments.append((str(value), None, None))
    return segments
