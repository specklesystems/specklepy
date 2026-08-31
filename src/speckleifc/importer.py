"""IFC → Speckle bundle: one ``ImportJob`` drives a :class:`BundleBuilder` directly.

Two passes over the file: the geometry iterator interns definitions/materials
(:mod:`~speckleifc.converter.node` managers over
:mod:`~speckleifc.converter.geometry`) and caches per-element placements, then the
spatial tree walk emits containers and object rows
(:mod:`~speckleifc.converter.object`). The relation-only sweeps
(:mod:`~speckleifc.converter.relation`) and the model-scoped rows
(:mod:`~speckleifc.converter.model`) run once at the end.
"""

from __future__ import annotations

import logging
import time
from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from ifcopenshell.ifcopenshell_wrapper import Triangulation, TriangulationElement

from speckleifc.converter import relation
from speckleifc.converter.geometry import transposed
from speckleifc.converter.model import emit_georeferencing
from speckleifc.converter.node import (
    DefinitionManager,
    GroupManager,
    LevelManager,
    MaterialManager,
    SystemManager,
)
from speckleifc.converter.object import Placement, convert_object
from speckleifc.ifc_geometry_processing import create_geometry_iterator
from speckleifc.ifc_openshell_helpers import get_children
from speckleifc.progress import ProgressReporter
from specklepy.bundle.builder import BundleBuilder, BundleContainer, BundleObject
from specklepy.bundle.envelope_writer import SceneViewKey
from specklepy.bundle.spec import Rel
from specklepy.logging.exceptions import SpeckleException

logger = logging.getLogger(__name__)


class ImportJob:
    def __init__(
        self, ifc_file: file, builder: BundleBuilder, progress: ProgressReporter
    ) -> None:
        self.ifc_file = ifc_file
        self.builder = builder
        self.progress = progress

        self._materials = MaterialManager(builder)
        self._definitions = DefinitionManager(builder, self._materials)
        self._levels = LevelManager(builder)
        self._systems = SystemManager(builder)
        self._groups = GroupManager(builder)

        self._placements: dict[int, Placement] = {}
        """step id → placement, filled by the geometry pre-pass"""
        self._current_level = None
        self._current_storey_name: str | None = None
        self._current_room: BundleObject | None = None

        self.geometries_count = 0
        self.geometries_used = 0
        self.elements_converted = 0

    @property
    def empty_meshes_skipped(self) -> int:
        return self._definitions.empty_meshes_skipped

    def run(self) -> None:
        start = time.time()
        self._pre_process_geometry()
        print(f"Geometry conversion complete after {(time.time() - start):.3f}s")
        print(f"Created {self.geometries_count} geometries")
        if self.empty_meshes_skipped:
            logger.info("Skipped %d empty style meshes", self.empty_meshes_skipped)
        self._convert_and_emit()

    def _convert_and_emit(self) -> None:
        start = time.time()
        self._convert_project_tree()
        print(f"Element tree conversion complete after {(time.time() - start):.3f}s")
        print(f"Used {self.geometries_used} geometries")

        self._systems.extract(self.ifc_file)
        self._groups.extract(self.ifc_file)
        relation.emit_connections(self.ifc_file, self.builder)
        relation.emit_hosting(self.ifc_file, self.builder)
        relation.emit_space_boundaries(self.ifc_file, self.builder)
        emit_georeferencing(self.ifc_file, self.builder)

        keys = [SceneViewKey.rel(Rel.ON_LEVEL)] if self._levels.has_levels else []
        self.builder.scene_view(
            "Level / Class", True, *keys, SceneViewKey.eav("ifcType")
        )

    # ── geometry pre-pass ────────────────────────────────────────────────────

    def _pre_process_geometry(self) -> None:
        iterator = create_geometry_iterator(self.ifc_file)
        if not iterator.initialize():
            raise SpeckleException("Failed to find any geometry in file")

        self.progress.report("Converting geometries", None)

        while True:
            shape = cast(TriangulationElement, iterator.get())
            self.geometries_count += 1
            step_id = cast(int, shape.id)
            try:
                definitions = self._definitions.definitions_for(
                    cast(Triangulation, shape.geometry)
                )
                if definitions:
                    matrix = shape.transformation.matrix
                    self._placements[step_id] = (transposed(matrix), definitions)
            except Exception as ex:
                raise SpeckleException(
                    f"Failed to convert geometry with id: {step_id}"
                ) from ex

            if self.progress.should_report_progress():
                self.progress.report(
                    f"Converted {self.geometries_count:,} geometries", None
                )
            if not iterator.next():
                break

    # ── spatial tree ─────────────────────────────────────────────────────────

    def _convert_project_tree(self) -> None:
        projects = self.ifc_file.by_type("IfcProject", False)
        if len(projects) != 1:
            raise SpeckleException("Expected exactly one IfcProject in file")

        self.progress.report("Converting elements", None)
        self._convert_element(projects[0], None, None, None)

    def _convert_element(
        self,
        element: entity_instance,
        parent_container: BundleContainer | None,
        parent_object: BundleObject | None,
        parent_element: entity_instance | None,
    ) -> None:
        try:
            self._convert(element, parent_container, parent_object, parent_element)
        except SpeckleException:
            raise
        except Exception as ex:
            raise SpeckleException(
                f"Failed to convert {element.is_a()} #{element.id()}"
            ) from ex

    def _convert(
        self,
        element: entity_instance,
        parent_container: BundleContainer | None,
        parent_object: BundleObject | None,
        parent_element: entity_instance | None,
    ) -> None:
        guid = cast(str, element.GlobalId)
        existing = self.builder.try_get_object(guid)
        if existing is not None and existing.properties_written:
            logger.warning(
                "Element %s (#%d) is reachable more than once; keeping the first "
                "conversion",
                guid,
                element.id(),
            )
            return

        previous_level = self._current_level
        previous_storey_name = self._current_storey_name
        previous_room = self._current_room

        if element.is_a("IfcBuildingStorey"):
            self._current_level = self._levels.get_or_add(element)
            self._current_storey_name = cast(str, element.Name or guid)

        if element.is_a("IfcProject") or element.is_a("IfcSpatialStructureElement"):
            self._convert_spatial(element, parent_container)
        else:
            self._convert_product(
                element, parent_container, parent_object, parent_element
            )

        self._current_level = previous_level
        self._current_storey_name = previous_storey_name
        self._current_room = previous_room

        self.elements_converted += 1
        if self.progress.should_report_progress():
            self.progress.report(
                f"Converted {self.elements_converted:,} elements", None
            )

    def _convert_spatial(
        self, element: entity_instance, parent_container: BundleContainer | None
    ) -> None:
        guid = cast(str, element.GlobalId)
        name = cast(str, element.Name or element.LongName or guid)
        container = self.builder.get_or_add_container(
            guid, name, parent_container, element.is_a()
        )
        if not element.is_a("IfcProject"):
            obj = self._emit_object(element, name)
            obj.collection = container
            if element.is_a("IfcSpace"):
                self._current_room = obj
        for child in get_children(element):
            if self._should_convert(child):
                self._convert_element(child, container, None, element)

    def _convert_product(
        self,
        element: entity_instance,
        parent_container: BundleContainer | None,
        parent_object: BundleObject | None,
        parent_element: entity_instance | None,
    ) -> None:
        obj = self._emit_object(element, cast(str, element.Name or element.GlobalId))

        if parent_object is not None:
            parent_object.add_child(obj)
            if parent_element is not None and parent_element.is_a("IfcElementAssembly"):
                parent_object.add_assembly_member(obj)
        elif parent_container is not None:
            obj.collection = parent_container

        if self._current_level is not None:
            self._levels.assign(obj, self._current_level)
        if self._current_room is not None:
            obj.room = self._current_room

        for child in get_children(element):
            if self._should_convert(child):
                self._convert_element(child, parent_container, obj, element)

    def _emit_object(self, element: entity_instance, name: str) -> BundleObject:
        placement = self._placements.get(element.id())
        if placement is not None:
            self.geometries_used += 1
        return convert_object(
            self.builder,
            element,
            name,
            storey_name=self._current_storey_name,
            placement=placement,
        )

    @staticmethod
    def _should_convert(element: entity_instance) -> bool:
        # Only IfcRoot entities (the GUID-carrying roots) are convertible; this
        # skips e.g. IfcGridAxis
        if not element.is_a("IfcRoot"):
            logger.debug(
                "Skipping #%d: %s is not an IfcRoot", element.id(), element.is_a()
            )
            return False
        return True
