"""Node-kind managers (the ``nodes`` namespace): one manager per node concern —
materials, definitions, levels, systems and groups — each writing through the
:class:`BundleBuilder`."""

from __future__ import annotations

import logging
from typing import Any, cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from ifcopenshell.ifcopenshell_wrapper import Triangulation

from speckleifc.converter.geometry import geometry_to_speckle
from specklepy.bundle.builder import (
    BundleBuilder,
    BundleDefinition,
    BundleLevel,
    BundleMaterial,
    BundleObject,
)
from specklepy.objects.other import RenderMaterial

logger = logging.getLogger(__name__)

# catalogued CONTAINER subtype (bundle_spec NODE_KINDS), shared with rvextract
MEP_SYSTEM_SUBTYPE = "MEP System"


class MaterialManager:
    """MATERIAL nodes: interns one node per distinct render style."""

    def __init__(self, builder: BundleBuilder) -> None:
        self._builder = builder

    def get_or_add(self, material: RenderMaterial, fallback_key: str) -> BundleMaterial:
        return self._builder.get_or_add_material(
            material.applicationId or fallback_key,
            material.name,
            int(material.diffuse),
            opacity=float(material.opacity),
        )


class DefinitionManager:
    """DEFINITION nodes: one definition per non-empty style mesh, interned once per
    triangulation (permissive-shape-reuse hands the same triangulation to every
    element sharing a representation)."""

    def __init__(self, builder: BundleBuilder, materials: MaterialManager) -> None:
        self._builder = builder
        self._materials = materials
        self._definitions_by_geometry: dict[str, list[BundleDefinition]] = {}
        self.empty_meshes_skipped = 0

    def definitions_for(self, geometry: Triangulation) -> list[BundleDefinition]:
        geometry_id = cast(str, geometry.id)
        cached = self._definitions_by_geometry.get(geometry_id)
        if cached is not None:
            return cached

        definitions: list[BundleDefinition] = []
        for mesh, material in geometry_to_speckle(geometry):
            if not mesh.faces:
                self.empty_meshes_skipped += 1
                continue
            mesh_id = mesh.applicationId
            assert mesh_id is not None
            handle = self._materials.get_or_add(material, mesh_id)

            def populate(
                definition: BundleDefinition,
                mesh: Any = mesh,
                mesh_id: str = mesh_id,
                handle: Any = handle,
            ) -> None:
                definition.add_geometry(mesh, geometry_key=mesh_id).material = handle

            definitions.append(
                self._builder.get_or_add_definition(mesh_id, mesh_id, populate)
            )
        self._definitions_by_geometry[geometry_id] = definitions
        return definitions


class LevelManager:
    """LEVEL nodes: one per storey, plus ON_LEVEL membership."""

    def __init__(self, builder: BundleBuilder) -> None:
        self._builder = builder
        self.has_levels = False

    def get_or_add(self, storey: entity_instance) -> BundleLevel:
        guid = cast(str, storey.GlobalId)
        elevation = getattr(storey, "Elevation", None)
        return self._builder.get_or_add_level(
            guid,
            cast(str, storey.Name or guid),
            float(elevation) if elevation is not None else 0.0,
        )

    def assign(self, obj: BundleObject, level: BundleLevel) -> None:
        obj.level = level
        self.has_levels = True


class SystemManager:
    """MEP System semantic containers + IN_SYSTEM membership, from IFC system
    grouping (``IfcSystem``/``IfcDistributionSystem`` via ``IfcRelAssignsToGroup``)."""

    def __init__(self, builder: BundleBuilder) -> None:
        self._builder = builder

    def extract(self, ifc_file: file) -> None:
        emitted: set[tuple[int, int]] = set()
        for rel in ifc_file.by_type("IfcRelAssignsToGroup"):
            group: entity_instance | None = rel.RelatingGroup
            if group is None or not group.is_a("IfcSystem"):
                continue
            guid = getattr(group, "GlobalId", None)
            if not guid:
                continue
            name = group.Name or guid
            system_type = getattr(group, "PredefinedType", None) or getattr(
                group, "ObjectType", None
            )
            display = name
            if system_type and system_type != name:
                display = f"{name} ({system_type})"
            system = self._builder.get_or_add_semantic_container(
                guid, display, None, MEP_SYSTEM_SUBTYPE
            )
            for member in rel.RelatedObjects or []:
                member_id = getattr(member, "GlobalId", None)
                if not member_id:
                    continue
                obj = self._builder.get_or_add_object(member_id)
                if (obj.k, system.k) not in emitted:
                    emitted.add((obj.k, system.k))
                    obj.add_to_system(system)


class GroupManager:
    """Group semantic containers + IN_GROUP membership, from plain ``IfcGroup``s."""

    def __init__(self, builder: BundleBuilder) -> None:
        self._builder = builder

    def extract(self, ifc_file: file) -> None:
        emitted: set[tuple[int, int]] = set()
        for rel in ifc_file.by_type("IfcRelAssignsToGroup"):
            group: entity_instance | None = rel.RelatingGroup
            if group is None or not group.is_a("IfcGroup") or group.is_a("IfcSystem"):
                continue
            guid = getattr(group, "GlobalId", None)
            if not guid:
                continue
            container = self._builder.get_or_add_semantic_container(
                guid, group.Name or guid, None, "Group"
            )
            for member in rel.RelatedObjects or []:
                member_id = getattr(member, "GlobalId", None)
                if not member_id:
                    continue
                obj = self._builder.try_get_object(member_id)
                if obj is None:
                    logger.debug(
                        "Group member %s was not converted; skipping IN_GROUP",
                        member_id,
                    )
                    continue
                if (obj.k, container.k) not in emitted:
                    emitted.add((obj.k, container.k))
                    obj.add_to_group(container)
