"""Project a received :class:`Model` onto the legacy Base tree (port of the .NET
``ObjectsArtifactReader``): a Collection root, DataObjects keyed by applicationId,
proxies for materials and instance definitions, ``version = 4``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from specklepy.bundle import sgeo
from specklepy.bundle.bundle_reader import ArtefactBundle, Geometry, Node
from specklepy.bundle.model import Model, parse_transform
from specklepy.bundle.spec import NodeKind
from specklepy.objects.base import Base
from specklepy.objects.data_objects import DataObject
from specklepy.objects.models.collections.collection import Collection
from specklepy.objects.models.units import get_scale_factor_from_string
from specklepy.objects.other import RenderMaterial
from specklepy.objects.proxies import (
    InstanceDefinitionProxy,
    InstanceProxy,
    RenderMaterialProxy,
)

if TYPE_CHECKING:
    from specklepy.bundle.property_table import PropertyView

IDENTITY = [
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
]


def to_base(model: Model) -> Collection:
    bundle = model.bundle
    rels = bundle.relations
    root, collection_by_node = _collection_tree(bundle.nodes)
    materials = _materials(bundle.nodes)
    object_by_geometry = rels.object_by_geometry()
    placements_by_object: dict[int, list[int]] = {}
    for e in rels.display_instance_edges:
        placements_by_object.setdefault(e.src, []).append(e.dst)

    for object_k, app_id in sorted(bundle.object_app_ids.items()):
        collection_k = rels.collection_by_object.get(object_k)
        host = (
            root if collection_k is None else collection_by_node.get(collection_k, root)
        )
        placements = placements_by_object.get(object_k)
        if placements:
            for i, instance_k in enumerate(placements):
                instance = bundle.nodes.get(instance_k)
                if instance is not None:
                    placement_id = app_id if i == 0 else f"{app_id}-instance-{i}"
                    host.elements.append(_instance_proxy(placement_id, instance))
            continue
        built = _geometry_object(model, object_k, app_id)
        if built is not None:
            host.elements.append(built)

    _attach_materials(bundle, object_by_geometry, materials, root)
    _attach_instance_definitions(model, object_by_geometry, root)

    reference_point = _reference_point_root_value(bundle)
    if reference_point is not None:
        root["referencePointTransform"] = reference_point
    root["units"] = bundle.units
    root["version"] = 4
    return root


def _collection_tree(
    nodes: dict[int, Node],
) -> tuple[Collection, dict[int, Collection]]:
    root = Collection(name="Received model", applicationId="artifact-root")
    root.id = "artifact-root"
    by_node: dict[int, Collection] = {}
    for k, n in nodes.items():
        if n.kind == NodeKind.CONTAINER:
            coll = Collection(name=n.name or "Layer", applicationId=f"coll-{k}")
            coll.id = coll.applicationId
            by_node[k] = coll
    for k, coll in by_node.items():
        def_ref = nodes[k].def_ref
        parent = by_node.get(def_ref) if def_ref is not None else None
        (parent or root).elements.append(coll)
    return root, by_node


def _materials(nodes: dict[int, Node]) -> dict[int, RenderMaterialProxy]:
    proxies: dict[int, RenderMaterialProxy] = {}
    for k, n in nodes.items():
        if n.kind != NodeKind.MATERIAL:
            continue
        material = RenderMaterial(
            name=n.name or "material",
            diffuse=n.argb if n.argb is not None else -1,
            opacity=n.opacity if n.opacity is not None else 1.0,
            metalness=n.metalness if n.metalness is not None else 0.0,
            roughness=n.roughness if n.roughness is not None else 1.0,
            emissive=n.emissive if n.emissive is not None else 0,
        )
        material.applicationId = f"mat-{k}"
        if n.ior is not None:
            material["ior"] = n.ior
        proxy = RenderMaterialProxy(value=material, objects=[])
        proxy.applicationId = proxy.id = f"mat-{k}"
        proxies[k] = proxy
    return proxies


def _attach_materials(
    bundle: ArtefactBundle,
    object_by_geometry: dict[int, int],
    materials: dict[int, RenderMaterialProxy],
    root: Collection,
) -> None:
    for geometry_k, material_k in bundle.relations.material_by_geometry.items():
        proxy = materials.get(material_k)
        object_k = object_by_geometry.get(geometry_k)
        app_id = bundle.object_app_ids.get(object_k) if object_k is not None else None
        if proxy is not None and app_id is not None and app_id not in proxy.objects:
            proxy.objects.append(app_id)
    used = [p for p in materials.values() if p.objects]
    if used:
        root["renderMaterialProxies"] = used


def _instance_proxy(app_id: str, instance: Node) -> InstanceProxy:
    proxy = InstanceProxy(
        definitionId=f"def-{instance.def_ref if instance.def_ref is not None else -1}",
        transform=parse_transform(instance.transform) or list(IDENTITY),
        maxDepth=0,
        units=instance.units or "none",
    )
    proxy.applicationId = proxy.id = app_id
    return proxy


def _attach_instance_definitions(
    model: Model, object_by_geometry: dict[int, int], root: Collection
) -> None:
    bundle = model.bundle
    rels = bundle.relations
    depth_by_definition = _definition_depths(bundle)
    proxies: list[InstanceDefinitionProxy] = []
    for definition_k, n in bundle.nodes.items():
        if n.kind != NodeKind.DEFINITION:
            continue
        members: list[str] = []
        for geometry_k in rels.defines_by_definition.get(definition_k, []):
            object_k = object_by_geometry.get(geometry_k)
            app_id = (
                bundle.object_app_ids.get(object_k) if object_k is not None else None
            )
            if app_id is not None:
                if app_id not in members:
                    members.append(app_id)
                continue
            geometry = model.geometries.get(geometry_k)
            geometry_id = f"def-geo-{geometry_k}"
            if geometry is not None and geometry.is_sgeo and geometry_id not in members:
                decoded = sgeo.decode(geometry.content)
                decoded.applicationId = geometry_id
                member = DataObject(
                    name="geometry", displayValue=[decoded], properties={}
                )
                member.applicationId = member.id = geometry_id
                root.elements.append(member)
                members.append(geometry_id)
        for instance_k in rels.defines_instance_by_definition.get(definition_k, []):
            instance = bundle.nodes.get(instance_k)
            if instance is None:
                continue
            nested_id = f"nested-inst-{instance_k}"
            root.elements.append(_instance_proxy(nested_id, instance))
            if nested_id not in members:
                members.append(nested_id)
        proxy = InstanceDefinitionProxy(
            name=n.name or f"Definition {definition_k}",
            objects=members,
            maxDepth=depth_by_definition.get(definition_k, 0),
        )
        proxy.applicationId = proxy.id = f"def-{definition_k}"
        proxies.append(proxy)
    if proxies:
        root["instanceDefinitionProxies"] = proxies


def _definition_depths(bundle: ArtefactBundle) -> dict[int, int]:
    """Deepest nesting level per DEFINITION, 0 at a top-level placement; consumers bake
    deepest-first."""
    depth: dict[int, int] = {}
    nodes = bundle.nodes
    nested = bundle.relations.defines_instance_by_definition

    def propagate(definition_k: int, d: int, on_stack: set[int]) -> None:
        if definition_k in on_stack:
            return
        on_stack.add(definition_k)
        if depth.get(definition_k, -1) < d:
            depth[definition_k] = d
            for instance_k in nested.get(definition_k, []):
                instance = nodes.get(instance_k)
                if instance is not None and instance.def_ref is not None:
                    propagate(instance.def_ref, d + 1, on_stack)
        on_stack.remove(definition_k)

    for e in bundle.relations.display_instance_edges:
        instance = nodes.get(e.dst)
        if instance is not None and instance.def_ref is not None:
            propagate(instance.def_ref, 0, set())
    return depth


def _geometry_object(model: Model, object_k: int, app_id: str) -> Base | None:
    bundle = model.bundle
    displays: list[Base] = []
    for e in sorted(bundle.relations.display_by_object(object_k), key=lambda e: e.ord):
        geometry = model.geometries.get(e.dst)
        if geometry is not None and geometry.is_sgeo:
            decoded = sgeo.decode(geometry.content)
            decoded.applicationId = app_id
            displays.append(decoded)
    if not displays:
        return None

    table = bundle.property_table
    obj = DataObject(
        name=table.get_string(object_k, "name") or app_id,
        displayValue=displays,
        properties=_merged_properties(
            table.under(object_k, "properties"),
            bundle.type_properties(object_k).under("properties"),
        ),
    )
    obj.applicationId = obj.id = app_id
    return obj


def _merged_properties(
    instance: PropertyView, type_: PropertyView
) -> dict[str, object]:
    merged = type_.to_nested()
    _overlay(merged, instance.to_nested())
    return merged


def _overlay(target: dict[str, object], source: dict[str, object]) -> None:
    for key, value in source.items():
        existing = target.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            _overlay(existing, value)
        else:
            target[key] = value


def _reference_point_root_value(bundle: ArtefactBundle) -> dict[str, object] | None:
    """The v1 root reference-point transform: only a bundle whose sender applied its
    datum to stored geometry carries one — the rigid inverse of
    ``modelPlacement.transform`` in the legacy layout (basis columns first, translation
    at 12–14, in feet)."""
    props = bundle.model_properties
    if props.get("modelPlacement.appliedToGeometry") is not True:
        return None
    transform = props.get("modelPlacement.transform")
    d = parse_transform(transform if isinstance(transform, str) else None)
    if d is None:
        return None
    units = str(props.get("modelPlacement.units") or bundle.units)
    to_feet = get_scale_factor_from_string(units, "ft") if units else 1.0
    tx, ty, tz = d[3] * to_feet, d[7] * to_feet, d[11] * to_feet
    matrix = [
        d[0], d[1], d[2], 0.0,
        d[4], d[5], d[6], 0.0,
        d[8], d[9], d[10], 0.0,
        -(d[0] * tx + d[4] * ty + d[8] * tz),
        -(d[1] * tx + d[5] * ty + d[9] * tz),
        -(d[2] * tx + d[6] * ty + d[10] * tz),
        1.0,
    ]  # fmt: skip
    return {"transform": matrix}


__all__ = ["to_base", "Geometry"]
