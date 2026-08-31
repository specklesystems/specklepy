"""Parse a downloaded bundle directory into dense-int tables (port of the .NET
``ArtefactBundleReader``, columnar profile)."""

from __future__ import annotations

from dataclasses import dataclass, field

from specklepy.bundle.envelope_writer import CameraView
from specklepy.bundle.parquet_table_reader import (
    ParquetTable,
    find_files,
    find_table,
    read_table,
)
from specklepy.bundle.property_table import PropertyTable, PropertyView, coalesce
from specklepy.bundle.spec import Rel

SGEO_MAGIC = b"SGEO"


@dataclass(frozen=True)
class RelationRow:
    rel: int
    src: int
    dst: int
    ord: int


@dataclass(frozen=True)
class Node:
    kind: int
    name: str | None
    def_ref: int | None
    transform: str | None
    units: str | None
    subtype: str | None
    argb: int | None
    opacity: float | None
    metalness: float | None
    roughness: float | None
    emissive: int | None
    ior: float | None
    elevation: float | None
    gh_topology: str | None


@dataclass(frozen=True)
class Geometry:
    content: bytes
    type: str | None

    @property
    def is_sgeo(self) -> bool:
        return self.content[:4] == SGEO_MAGIC


@dataclass(frozen=True)
class SceneViewTier:
    source: str
    ref: str


@dataclass(frozen=True)
class PropertySetField:
    set_name: str
    set_key: str
    set_description: str | None
    field_name: str
    field_bucket_id: str | None
    data_type: str | None
    default_string: str | None
    default_double: float | None
    default_boolean: bool | None
    unit: str | None
    description: str | None
    applies_to: str | None


_OBJECT_NODE_RELS = {
    int(Rel.ON_LEVEL),
    int(Rel.IN_COLLECTION),
    int(Rel.IN_MODEL),
    int(Rel.IN_ROOM),
    int(Rel.IN_SYSTEM),
    int(Rel.IN_GROUP),
    int(Rel.IN_ASSEMBLY),
}


@dataclass
class Relations:
    display: list[RelationRow] = field(default_factory=list)
    solid_by_object: dict[int, list[int]] = field(default_factory=dict)
    subelement: list[RelationRow] = field(default_factory=list)
    defines_by_definition: dict[int, list[int]] = field(default_factory=dict)
    defines_ord_by_definition: dict[int, list[int]] = field(default_factory=dict)
    material_by_geometry: dict[int, int] = field(default_factory=dict)
    material_by_instance: dict[int, int] = field(default_factory=dict)
    color_by_geometry: dict[int, int] = field(default_factory=dict)
    color_by_object: dict[int, int] = field(default_factory=dict)
    display_instance_edges: list[RelationRow] = field(default_factory=list)
    defines_instance_by_definition: dict[int, list[int]] = field(default_factory=dict)
    collection_by_object: dict[int, int] = field(default_factory=dict)
    in_room: list[RelationRow] = field(default_factory=list)
    groups_by_object: dict[int, list[int]] = field(default_factory=dict)
    systems_by_object: dict[int, list[int]] = field(default_factory=dict)
    in_assembly: list[RelationRow] = field(default_factory=list)
    connects_to: list[RelationRow] = field(default_factory=list)
    hosted_on: list[RelationRow] = field(default_factory=list)
    bounds: list[RelationRow] = field(default_factory=list)
    places_by_object: dict[int, int] = field(default_factory=dict)
    member_objects_by_definition: dict[int, list[int]] = field(default_factory=dict)
    member_ord_by_definition: dict[int, list[int]] = field(default_factory=dict)
    material_by_object: dict[int, int] = field(default_factory=dict)
    material_by_node: dict[int, int] = field(default_factory=dict)
    color_by_node: dict[int, int] = field(default_factory=dict)
    object_node_by_rel: dict[int, dict[int, int]] = field(default_factory=dict)
    unknown_rels: set[int] = field(default_factory=set)
    _display_by_object: dict[int, list[RelationRow]] | None = None

    def display_by_object(self, object_k: int) -> list[RelationRow]:
        if self._display_by_object is None:
            grouped: dict[int, list[RelationRow]] = {}
            for row in self.display:
                grouped.setdefault(row.src, []).append(row)
            self._display_by_object = grouped
        return self._display_by_object.get(object_k, [])

    def object_by_geometry(self) -> dict[int, int]:
        return {row.dst: row.src for row in self.display}


@dataclass
class ArtefactBundle:
    object_app_ids: dict[int, str]
    property_table: PropertyTable
    type_property_table: PropertyTable
    type_index_by_object: dict[int, int]
    nodes: dict[int, Node]
    relations: Relations
    units: str
    default_scene_view: list[SceneViewTier]
    camera_views: list[CameraView]
    model_properties: dict[str, object]
    property_set_definitions: list[PropertySetField]
    geometries: dict[int, Geometry]

    def type_properties(self, object_k: int) -> PropertyView:
        type_k = self.type_index_by_object.get(object_k)
        if type_k is None:
            return self.type_property_table.view(-1)
        return self.type_property_table.view(type_k)


def read_bundle(directory: str, *, load_geometry: bool = False) -> ArtefactBundle:
    objects = _required(directory, ".eav.objects.parquet")
    paths = _required(directory, ".eav.paths.parquet")
    eav = _required(directory, ".eav.eav.parquet")
    nodes = _required(directory, ".envelope.nodes.parquet")
    relations = _required(directory, ".envelope.relations.parquet")
    type_eav = find_table(directory, ".eav.type_eav.parquet", required=False)
    object_type = find_table(directory, ".eav.object_type.parquet", required=False)
    scene_views = find_table(directory, ".envelope.scene_views.parquet", required=False)
    camera_views = find_table(
        directory, ".envelope.camera_views.parquet", required=False
    )
    model = find_table(directory, ".eav.model.parquet", required=False)
    pset_defs = find_table(
        directory, ".eav.property_set_definitions.parquet", required=False
    )

    property_table = PropertyTable.load(eav, paths, "object_index")
    return ArtefactBundle(
        object_app_ids=_object_app_ids(objects),
        property_table=property_table,
        type_property_table=PropertyTable.load(type_eav, paths, "type_index"),
        type_index_by_object=_type_index(object_type),
        nodes=_nodes(nodes),
        relations=_relations(relations),
        units=_units(property_table),
        default_scene_view=_default_scene_view(scene_views),
        camera_views=_camera_views(camera_views),
        model_properties=_model_properties(model),
        property_set_definitions=_property_set_definitions(pset_defs),
        geometries=read_geometries(directory) if load_geometry else {},
    )


def _required(directory: str, suffix: str) -> ParquetTable:
    table = find_table(directory, suffix, required=True)
    assert table is not None
    return table


def read_geometries(directory: str) -> dict[int, Geometry]:
    shards = find_files(directory, "*.geometries*.parquet")
    if not shards:
        raise FileNotFoundError(f"bundle has no geometry shards in {directory}")
    result: dict[int, Geometry] = {}
    for shard in shards:
        table = read_table(shard)
        for k, content, type_ in zip(
            table.ints("geometryIndex"),
            table.blobs("content"),
            table.strings("type"),
            strict=True,
        ):
            if content is not None:
                result[k] = Geometry(content, type_)
    return result


def _object_app_ids(t: ParquetTable) -> dict[int, str]:
    return {
        k: app_id if app_id is not None else str(k)
        for k, app_id in zip(
            t.ints("object_index"), t.strings("application_id"), strict=True
        )
    }


def _type_index(t: ParquetTable | None) -> dict[int, int]:
    if t is None or not t.has("object_index"):
        return {}
    return dict(zip(t.ints("object_index"), t.ints("type_index"), strict=True))


def _nodes(t: ParquetTable) -> dict[int, Node]:
    cols = {
        "name": t.strings("name"),
        "def_ref": t.nullable_ints("def_ref"),
        "transform": t.strings("transform"),
        "units": t.strings("units"),
        "subtype": t.strings("subtype"),
        "argb": t.nullable_ints("argb"),
        "opacity": t.doubles("opacity"),
        "metalness": t.doubles("metalness"),
        "roughness": t.doubles("roughness"),
        "emissive": t.nullable_ints("emissive"),
        "ior": t.doubles("ior"),
        "elevation": t.doubles("elevation"),
        "gh_topology": t.strings("gh_topology"),
    }
    ids = t.ints("id")
    kinds = t.ints("kind")
    return {
        ids[i]: Node(kind=kinds[i], **{name: col[i] for name, col in cols.items()})
        for i in range(len(ids))
    }


def _relations(t: ParquetTable) -> Relations:
    r = Relations()
    rows = zip(t.ints("rel"), t.ints("src"), t.ints("dst"), t.ints("ord"), strict=True)
    for rel, src, dst, ord in rows:
        row = RelationRow(rel, src, dst, ord)
        if rel == Rel.DISPLAY:
            r.display.append(row)
        elif rel == Rel.SOLID:
            r.solid_by_object.setdefault(src, []).append(dst)
        elif rel == Rel.SUBELEMENT:
            r.subelement.append(row)
        elif rel == Rel.DEFINES:
            r.defines_by_definition.setdefault(src, []).append(dst)
            r.defines_ord_by_definition.setdefault(src, []).append(ord)
        elif rel == Rel.HAS_MATERIAL:
            # ord == 1 is the pre-spec instance-source tag
            (r.material_by_instance if ord == 1 else r.material_by_geometry)[src] = dst
        elif rel == Rel.HAS_COLOR:
            (r.color_by_object if ord == 1 else r.color_by_geometry)[src] = dst
        elif rel == Rel.DISPLAY_INSTANCE:
            r.display_instance_edges.append(row)
        elif rel == Rel.DEFINES_INSTANCE:
            r.defines_instance_by_definition.setdefault(src, []).append(dst)
        elif rel == Rel.IN_COLLECTION:
            r.collection_by_object[src] = dst
        elif rel == Rel.IN_ROOM:
            r.in_room.append(row)
        elif rel == Rel.IN_GROUP:
            r.groups_by_object.setdefault(src, []).append(dst)
        elif rel == Rel.IN_SYSTEM:
            r.systems_by_object.setdefault(src, []).append(dst)
        elif rel == Rel.IN_ASSEMBLY:
            r.in_assembly.append(row)
        elif rel == Rel.CONNECTS_TO:
            r.connects_to.append(row)
        elif rel == Rel.HOSTED_ON:
            r.hosted_on.append(row)
        elif rel == Rel.BOUNDS:
            r.bounds.append(row)
        elif rel == Rel.PLACES:
            r.places_by_object[src] = dst
        elif rel == Rel.DEFINES_MEMBER:
            r.member_objects_by_definition.setdefault(src, []).append(dst)
            r.member_ord_by_definition.setdefault(src, []).append(ord)
        elif rel == Rel.OBJECT_HAS_MATERIAL:
            r.material_by_object[src] = dst
        elif rel == Rel.OBJECT_HAS_COLOR:
            r.color_by_object[src] = dst
        elif rel == Rel.NODE_HAS_MATERIAL:
            r.material_by_node[src] = dst
        elif rel == Rel.NODE_HAS_COLOR:
            r.color_by_node[src] = dst
        elif rel not in (Rel.ON_LEVEL, Rel.IN_MODEL):
            r.unknown_rels.add(rel)
        if rel in _OBJECT_NODE_RELS:
            # first-wins so multi-valued rels (IN_SYSTEM) resolve deterministically
            r.object_node_by_rel.setdefault(rel, {}).setdefault(src, dst)
    return r


def _units(props: PropertyTable) -> str:
    for _, value in props.values_of("units"):
        if isinstance(value, str) and value:
            return value
    return ""


def _default_scene_view(t: ParquetTable | None) -> list[SceneViewTier]:
    if t is None or not t.has("source"):
        return []
    rows = zip(
        t.bools("is_default"),
        t.ints("ord"),
        t.strings("source"),
        t.strings("ref"),
        strict=True,
    )
    tiers = [(ord, source or "", ref or "") for d, ord, source, ref in rows if d]
    return [SceneViewTier(source, ref) for _, source, ref in sorted(tiers)]


def _camera_views(t: ParquetTable | None) -> list[CameraView]:
    if t is None or not t.has("pos_x"):
        return []
    views = [
        CameraView(
            view=v,
            name=name,
            is_default=bool(is_default),
            ord=ord,
            pos_x=px,
            pos_y=py,
            pos_z=pz,
            forward_x=fx,
            forward_y=fy,
            forward_z=fz,
            up_x=ux,
            up_y=uy,
            up_z=1.0 if uz is None else uz,
            target_x=tx,
            target_y=ty,
            target_z=tz,
            units=units,
            is_ortho=bool(is_ortho),
            fov=fov,
            lens_mm=lens,
            ortho_height=ortho,
            aspect=aspect,
            near=near,
            far=far,
        )
        for (
            v,
            name,
            is_default,
            ord,
            px,
            py,
            pz,
            fx,
            fy,
            fz,
            ux,
            uy,
            uz,
            tx,
            ty,
            tz,
            units,
            is_ortho,
            fov,
            lens,
            ortho,
            aspect,
            near,
            far,
        ) in zip(
            t.ints("view"),
            t.strings("name"),
            t.bools("is_default"),
            t.nullable_ints("ord"),
            t.doubles("pos_x"),
            t.doubles("pos_y"),
            t.doubles("pos_z"),
            t.doubles("forward_x"),
            t.doubles("forward_y"),
            t.doubles("forward_z"),
            t.doubles("up_x"),
            t.doubles("up_y"),
            t.doubles("up_z"),
            t.doubles("target_x"),
            t.doubles("target_y"),
            t.doubles("target_z"),
            t.strings("units"),
            t.bools("is_ortho"),
            t.doubles("fov"),
            t.doubles("lens_mm"),
            t.doubles("ortho_height"),
            t.doubles("aspect"),
            t.doubles("near"),
            t.doubles("far"),
            strict=True,
        )
    ]
    views.sort(key=lambda c: (c.ord if c.ord is not None else 2**31, c.view))
    return views


def _model_properties(t: ParquetTable | None) -> dict[str, object]:
    if t is None or not t.has("path"):
        return {}
    rows = zip(
        t.strings("path"),
        t.strings("value_string"),
        t.doubles("value_double"),
        t.bools("value_boolean"),
        strict=True,
    )
    result: dict[str, object] = {}
    for path, s, d, b in rows:
        value = coalesce(b, d, s)
        if path and value is not None:
            result[path] = value
    return result


def _property_set_definitions(t: ParquetTable | None) -> list[PropertySetField]:
    if t is None or not t.has("set_name"):
        return []
    return [
        PropertySetField(*row)
        for row in zip(
            t.strings("set_name"),
            t.strings("set_key"),
            t.strings("set_description"),
            t.strings("field_name"),
            t.strings("field_bucket_id"),
            t.strings("data_type"),
            t.strings("default_string"),
            t.doubles("default_double"),
            t.bools("default_boolean"),
            t.strings("unit"),
            t.strings("description"),
            t.strings("applies_to"),
            strict=True,
        )
    ]
