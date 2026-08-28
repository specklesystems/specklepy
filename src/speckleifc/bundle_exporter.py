"""Drives a :class:`BundleBuilder` from a converted IFC tree.

The IFC ``ImportJob.convert()`` returns a root ``Collection`` whose scene tree
(collections + DataObjects + InstanceProxy displayValues) and proxy lists
(instanceDefinitionProxies / renderMaterialProxies / levelProxies / systemProxies /
connectionProxies) map directly onto the bundle graph. Definitions and materials are
emitted first so placements and material edges can reference them.
"""

from __future__ import annotations

from typing import Any

from specklepy.bundle.builder import (
    BundleBuilder,
    BundleContainer,
    BundleGeometry,
    BundleObject,
)
from specklepy.bundle.envelope_writer import SceneViewKey
from specklepy.bundle.spec import Rel
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject
from specklepy.objects.geometry import Mesh
from specklepy.objects.models.collections.collection import Collection

_DEFINITION_GEOMETRY = "definitionGeometry"


def _attr(node: Base, key: str, default: Any = None) -> Any:
    try:
        return node[key]
    except (KeyError, AttributeError):
        return getattr(node, key, default)


class IfcBundleExporter:
    def __init__(self, builder: BundleBuilder) -> None:
        self._b = builder
        self._has_levels = False
        self._geometry_by_mesh_id: dict[str, BundleGeometry] = {}

    def export(self, root: Collection) -> int:
        """Emit the whole tree into the builder; returns the interned object count."""
        mesh_by_id = self._index_definition_geometry(root)
        self._emit_definitions(root, mesh_by_id)
        self._emit_materials(root)
        self._walk(root, parent_collection=None, parent_object=None, ord=0)
        self._emit_levels(root)
        self._emit_systems(root)
        self._emit_connections(root)
        keys = [SceneViewKey.rel(Rel.ON_LEVEL)] if self._has_levels else []
        self._b.scene_view("Level / Class", True, *keys, SceneViewKey.eav("ifcType"))
        return len(self._b.objects)

    # ── geometry / definitions ──────────────────────────────────────────────

    def _index_definition_geometry(self, root: Collection) -> dict[str, Mesh]:
        meshes: dict[str, Mesh] = {}
        for child in _attr(root, "elements", []) or []:
            if not isinstance(child, Collection):
                continue
            if _attr(child, "name") == _DEFINITION_GEOMETRY:
                for mesh in _attr(child, "elements", []) or []:
                    app_id = _attr(mesh, "applicationId")
                    if app_id and isinstance(mesh, Mesh):
                        meshes[app_id] = mesh
        return meshes

    def _emit_definitions(self, root: Collection, mesh_by_id: dict[str, Mesh]) -> None:
        for proxy in _attr(root, "instanceDefinitionProxies", []) or []:
            def_id = _attr(proxy, "applicationId")
            if not def_id:
                continue
            mesh_ids = [m for m in _attr(proxy, "objects", []) or [] if m in mesh_by_id]

            def populate(definition, ids=mesh_ids) -> None:
                for mesh_id in ids:
                    self._geometry_by_mesh_id[mesh_id] = definition.add_geometry(
                        mesh_by_id[mesh_id], geometry_key=mesh_id
                    )

            self._b.get_or_add_definition(def_id, _attr(proxy, "name"), populate)

    def _emit_materials(self, root: Collection) -> None:
        for proxy in _attr(root, "renderMaterialProxies", []) or []:
            material = _attr(proxy, "value")
            if material is None:
                continue
            handle = self._b.get_or_add_material(
                _attr(material, "applicationId") or _attr(material, "name") or "",
                _attr(material, "name"),
                int(_attr(material, "diffuse", -1)),
                opacity=float(_attr(material, "opacity", 1.0)),
                metalness=float(_attr(material, "metalness", 0.0)),
                roughness=float(_attr(material, "roughness", 1.0)),
                emissive=int(_attr(material, "emissive", 0)),
            )
            for mesh_id in _attr(proxy, "objects", []) or []:
                geometry = self._geometry_by_mesh_id.get(mesh_id)
                if geometry is not None:
                    geometry.material = handle

    # ── scene tree ──────────────────────────────────────────────────────────

    def _walk(
        self,
        node: Base,
        parent_collection: BundleContainer | None,
        parent_object: BundleObject | None,
        ord: int,
    ) -> None:
        if isinstance(node, Collection):
            if _attr(node, "name") == _DEFINITION_GEOMETRY:
                return
            container = self._b.get_or_add_container(
                _attr(node, "applicationId") or _attr(node, "name") or "collection",
                _attr(node, "name"),
                parent_collection,
                _attr(node, "ifcType") or "Collection",
            )
            for i, child in enumerate(_attr(node, "elements", []) or []):
                self._walk(child, container, None, i)
            return

        if isinstance(node, DataObject):
            app_id = _attr(node, "applicationId")
            if not app_id:
                return
            obj = self._b.get_or_add_object(app_id)
            obj.set_properties(
                _attr(node, "properties", {}) or {},
                name=_attr(node, "name"),
                speckle_type=node.speckle_type,
                root_scalars=[("ifcType", _attr(node, "ifcType"))],
            )
            if parent_object is not None:
                parent_object.add_child(obj, ord)
            elif parent_collection is not None:
                obj.collection = parent_collection
            self._emit_display(node, obj)
            for i, child in enumerate(_attr(node, "@elements", []) or []):
                self._walk(child, parent_collection, obj, i)

    def _emit_display(self, node: DataObject, obj: BundleObject) -> None:
        for i, ip in enumerate(_attr(node, "displayValue", []) or []):
            definition = self._b.try_get_definition(_attr(ip, "definitionId") or "")
            if definition is None:
                continue
            transform = _attr(ip, "transform", []) or []
            if len(transform) != 16:
                continue
            obj.place(
                definition,
                transform,
                _attr(ip, "units"),
                key=_attr(ip, "applicationId") or f"{obj.k}:{i}",
            )

    # ── levels / topology ───────────────────────────────────────────────────

    def _emit_levels(self, root: Collection) -> None:
        for proxy in _attr(root, "levelProxies", []) or []:
            level_id = _attr(proxy, "applicationId")
            if not level_id:
                continue
            value = _attr(proxy, "value")
            name = _attr(value, "name") if value is not None else None
            level = self._b.get_or_add_level(level_id, name, _elevation_of(value))
            for member_id in _attr(proxy, "objects", []) or []:
                self._b.get_or_add_object(member_id).level = level
                self._has_levels = True

    def _emit_systems(self, root: Collection) -> None:
        for proxy in _attr(root, "systemProxies", []) or []:
            system_id = _attr(proxy, "applicationId")
            if not system_id:
                continue
            name = _attr(proxy, "name")
            system_type = _attr(proxy, "systemType")
            display = name
            if system_type and system_type != name:
                display = f"{name} ({system_type})"
            system = self._b.get_or_add_container(
                system_id, display, None, "MEP System"
            )
            for member_id in _attr(proxy, "objects", []) or []:
                self._b.get_or_add_object(member_id).system = system

    def _emit_connections(self, root: Collection) -> None:
        for proxy in _attr(root, "connectionProxies", []) or []:
            source_id = _attr(proxy, "sourceAppId")
            target_id = _attr(proxy, "targetAppId")
            if not source_id or not target_id:
                continue
            source = self._b.get_or_add_object(source_id)
            target = self._b.get_or_add_object(target_id)
            src_flow = _attr(proxy, "sourceFlowDirection")
            tgt_flow = _attr(proxy, "targetFlowDirection")
            # SOURCE→SINK is directed; anything else is undirected → reciprocal pair
            if src_flow == "SOURCE" and tgt_flow == "SINK":
                source.connect_to(target)
            elif src_flow == "SINK" and tgt_flow == "SOURCE":
                target.connect_to(source)
            else:
                source.connect_to(target)
                target.connect_to(source)


def _elevation_of(level_value: Base | None) -> float:
    if level_value is None:
        return 0.0
    properties = _attr(level_value, "properties", {}) or {}
    attributes = properties.get("Attributes") if isinstance(properties, dict) else None
    elevation = attributes.get("Elevation") if isinstance(attributes, dict) else None
    try:
        return float(elevation) if elevation is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
