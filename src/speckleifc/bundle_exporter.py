"""Drives the Speckle 4.0 bundle producer from a converted IFC tree.

The IFC ``ImportJob.convert()`` returns a root ``Collection`` whose scene tree
(collections + DataObjects + InstanceProxy displayValues) and attached proxy lists
(instanceDefinitionProxies / renderMaterialProxies / levelProxies / systemProxies /
connectionProxies) map directly onto the envelope graph. This module performs that
mapping via :class:`~specklepy.bundle.pipeline.ObjectsArtifactPipeline` — no re-reading of
the IFC file; everything comes from the already-converted ``Base`` tree.

Emission order matters: definitions (+ their geometries) and materials first, so the scene
walk's instances and the material edges can reference the geometry/definition Ks already
minted.
"""

from __future__ import annotations

from typing import Any

from specklepy.bundle.envelope_writer import SceneView, SceneViewKey
from specklepy.bundle.pipeline import ObjectsArtifactPipeline
from specklepy.bundle.spec import Rel
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject
from specklepy.objects.geometry import Mesh
from specklepy.objects.models.collections.collection import Collection

_DEFINITION_GEOMETRY = "definitionGeometry"


def _attr(node: Base, key: str, default: Any = None) -> Any:
    """Read a typed or dynamic Base member, tolerating absence."""
    try:
        return node[key]
    except (KeyError, AttributeError):
        return getattr(node, key, default)


class IfcBundleExporter:
    """Translates a converted IFC root Collection into a bundle on disk."""

    def __init__(self, output_dir: str, base_name: str) -> None:
        self._pipeline = ObjectsArtifactPipeline(output_dir, base_name)
        self._def_k_by_id: dict[str, int] = {}
        self._object_count = 0
        self._has_levels = False

    def export(self, root: Collection) -> tuple[str, int]:
        """Emit the whole bundle. Returns ``(root_id, object_count)`` for the uploader."""
        mesh_by_id = self._index_definition_geometry(root)

        self._emit_definitions(root, mesh_by_id)
        self._emit_materials(root)
        self._walk(
            root, parent_collection_k=None, parent_object_k=None, ord=0, is_root=True
        )
        self._emit_levels(root)
        self._emit_systems(root)
        self._emit_connections(root)
        self._emit_default_scene_view()

        self._pipeline.complete()
        root_id = _attr(root, "applicationId") or "root"
        return root_id, self._object_count

    # ── geometry / definitions ──────────────────────────────────────────────

    def _index_definition_geometry(self, root: Collection) -> dict[str, Mesh]:
        """Build {mesh.applicationId -> Mesh} from the appended ``definitionGeometry`` collection."""
        index: dict[str, Mesh] = {}
        for el in _attr(root, "elements", []) or []:
            if isinstance(el, Collection) and _attr(el, "name") == _DEFINITION_GEOMETRY:
                for mesh in _attr(el, "elements", []) or []:
                    app_id = _attr(mesh, "applicationId")
                    if app_id:
                        index[app_id] = mesh
        return index

    def _emit_definitions(self, root: Collection, mesh_by_id: dict[str, Mesh]) -> None:
        for proxy in _attr(root, "instanceDefinitionProxies", []) or []:
            def_id = _attr(proxy, "applicationId")
            if not def_id:
                continue
            def_k = self._pipeline.add_definition(def_id, _attr(proxy, "name"))
            self._def_k_by_id[def_id] = def_k
            for ordi, mesh_id in enumerate(_attr(proxy, "objects", []) or []):
                mesh = mesh_by_id.get(mesh_id)
                if mesh is None:
                    continue
                geo_k = self._pipeline.add_geometry(mesh_id, mesh)
                self._pipeline.defines(def_k, geo_k, ordi)

    def _emit_materials(self, root: Collection) -> None:
        for proxy in _attr(root, "renderMaterialProxies", []) or []:
            material = _attr(proxy, "value")
            if material is None:
                continue
            mat_id = _attr(material, "applicationId") or _attr(material, "name") or ""
            mat_k = self._pipeline.add_material(
                mat_id,
                argb=int(_attr(material, "diffuse", -1)),
                opacity=float(_attr(material, "opacity", 1.0)),
                metalness=float(_attr(material, "metalness", 0.0)),
                roughness=float(_attr(material, "roughness", 1.0)),
            )
            for mesh_id in _attr(proxy, "objects", []) or []:
                geo_k = self._pipeline.intern_geometry_id(mesh_id)
                self._pipeline.has_material(geo_k, mat_k)

    # ── scene tree ──────────────────────────────────────────────────────────

    def _walk(
        self,
        node: Base,
        parent_collection_k: int | None,
        parent_object_k: int | None,
        ord: int,
        is_root: bool = False,
    ) -> None:
        if isinstance(node, Collection):
            if _attr(node, "name") == _DEFINITION_GEOMETRY:
                return  # definition geometry, not a scene container
            coll_k = self._pipeline.add_collection(
                _attr(node, "applicationId") or _attr(node, "name") or "collection",
                _attr(node, "name"),
                parent_collection_k,
                _attr(node, "ifcType") or "Collection",
            )
            for i, child in enumerate(_attr(node, "elements", []) or []):
                self._walk(child, coll_k, None, i)
            return

        if isinstance(node, DataObject):
            app_id = _attr(node, "applicationId")
            if not app_id:
                return
            obj_k = self._pipeline.intern_object(app_id)
            self._object_count += 1
            self._pipeline.add_properties(
                app_id,
                _attr(node, "properties", {}) or {},
                root_scalars=[
                    ("name", _attr(node, "name")),
                    ("ifcType", _attr(node, "ifcType")),
                ],
            )

            # membership: under a Collection -> IN_COLLECTION; under a DataObject -> SUBELEMENT.
            if parent_object_k is not None:
                self._pipeline.subelement(parent_object_k, obj_k, ord)
            elif parent_collection_k is not None:
                self._pipeline.in_collection(obj_k, parent_collection_k, ord)

            self._emit_display(node, obj_k)

            for i, child in enumerate(_attr(node, "@elements", []) or []):
                self._walk(child, parent_collection_k, obj_k, i)
            return

        # Meshes / geometry primitives appearing inline are skipped (definition geometry
        # is handled via the proxies above).

    def _emit_display(self, node: DataObject, obj_k: int) -> None:
        for i, ip in enumerate(_attr(node, "displayValue", []) or []):
            def_id = _attr(ip, "definitionId")
            def_k = self._def_k_by_id.get(def_id) if def_id else None
            if def_k is None:
                continue
            inst_k = self._pipeline.add_instance(
                _attr(ip, "applicationId") or f"{obj_k}:{i}",
                def_k,
                _attr(ip, "transform", []) or [],
                _attr(ip, "units"),
            )
            self._pipeline.display_instance(obj_k, inst_k, i)

    # ── levels / topology ─────────────────────────────────────────────────────

    def _emit_levels(self, root: Collection) -> None:
        for proxy in _attr(root, "levelProxies", []) or []:
            level_id = _attr(proxy, "applicationId")
            if not level_id:
                continue
            value = _attr(proxy, "value")
            name = _attr(value, "name") if value is not None else None
            lvl_k = self._pipeline.add_level(level_id, name, _elevation_of(value))
            for member_id in _attr(proxy, "objects", []) or []:
                obj_k = self._pipeline.intern_object(member_id)
                self._pipeline.on_level(obj_k, lvl_k)
                self._has_levels = True

    def _emit_default_scene_view(self) -> None:
        """Author the producer's default scene-explorer grouping: Level > IFC class.

        Tier 1 walks the ON_LEVEL relation (group by storey); tier 2 groups by the
        ``ifcType`` eav attribute (the IFC class). The consumer seeds its model-tree
        grouping from this. The Level tier is omitted when the file has no storeys, so
        the default degrades to grouping by class alone.
        """
        keys = []
        if self._has_levels:
            keys.append(SceneViewKey.rel(Rel.ON_LEVEL))
        keys.append(SceneViewKey.eav("ifcType"))
        self._pipeline.add_scene_view(
            SceneView(view=0, name="Level / Class", is_default=True, keys=keys)
        )

    def _emit_systems(self, root: Collection) -> None:
        for proxy in _attr(root, "systemProxies", []) or []:
            system_id = _attr(proxy, "applicationId")
            if not system_id:
                continue
            name = _attr(proxy, "name")
            system_type = _attr(proxy, "systemType")
            # Canonical container subtype stays "System" (cross-connector); the IFC system type
            # (PredefinedType/ObjectType) rides on the display name so it isn't lost — but only when
            # it adds information (some exports set ObjectType == Name, e.g. "S_PWC").
            display = f"{name} ({system_type})" if system_type and system_type != name else name
            sys_k = self._pipeline.add_container(system_id, display, None, "System")
            for member_id in _attr(proxy, "objects", []) or []:
                obj_k = self._pipeline.intern_object(member_id)
                self._pipeline.in_system(obj_k, sys_k, 0)

    def _emit_connections(self, root: Collection) -> None:
        for proxy in _attr(root, "connectionProxies", []) or []:
            source_id = _attr(proxy, "sourceAppId")
            target_id = _attr(proxy, "targetAppId")
            if not source_id or not target_id:
                continue
            src_k = self._pipeline.intern_object(source_id)
            tgt_k = self._pipeline.intern_object(target_id)
            src_flow = _attr(proxy, "sourceFlowDirection")
            tgt_flow = _attr(proxy, "targetFlowDirection")

            # Orient by FlowDirection: SOURCE->SINK is a directed edge (flip if reversed);
            # anything else (SOURCEANDSINK / NOTDEFINED / missing) is undirected -> reciprocal pair.
            if src_flow == "SOURCE" and tgt_flow == "SINK":
                self._pipeline.connects_to(src_k, tgt_k)
            elif src_flow == "SINK" and tgt_flow == "SOURCE":
                self._pipeline.connects_to(tgt_k, src_k)
            else:
                self._pipeline.connects_to(src_k, tgt_k)
                self._pipeline.connects_to(tgt_k, src_k)


def _elevation_of(level_value: Base | None) -> float:
    """Best-effort storey elevation from the level DataObject's IFC attributes."""
    if level_value is None:
        return 0.0
    props = _attr(level_value, "properties", {}) or {}
    attributes = props.get("Attributes", {}) if isinstance(props, dict) else {}
    elevation = attributes.get("Elevation") if isinstance(attributes, dict) else None
    try:
        return float(elevation) if elevation is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
