import time
from dataclasses import dataclass, field
from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from ifcopenshell.ifcopenshell_wrapper import TriangulationElement

from speckleifc.converter.data_object_converter import data_object_to_speckle
from speckleifc.converter.geometry_converter import geometry_to_speckle
from speckleifc.converter.project_converter import project_to_speckle
from speckleifc.converter.spatial_element_converter import spatial_element_to_speckle
from speckleifc.ifc_geometry_processing import create_geometry_iterator
from speckleifc.ifc_openshell_helpers import get_children
from speckleifc.level_proxy_manager import LevelProxyManager
from speckleifc.render_material_proxy_manager import RenderMaterialProxyManager
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects import Base
from specklepy.objects.data_objects import DataObject


@dataclass
class ImportJob:
    ifc_file: file
    cached_display_values: dict[int, list[Base]] = field(default_factory=dict)  # noqa: F821
    _render_material_manager: RenderMaterialProxyManager = field(
        default_factory=lambda: RenderMaterialProxyManager()
    )
    _level_proxy_manager: LevelProxyManager = field(
        default_factory=lambda: LevelProxyManager()
    )
    geometries_count: int = 0
    geometries_used: int = 0
    _current_storey_data_object: DataObject | None = field(default=None, init=False)

    def convert_element(self, step_element: entity_instance) -> Base:
        # Track current storey context and store for level proxies
        previous_storey_data_object = self._current_storey_data_object
        if step_element.is_a("IfcBuildingStorey"):
            # Convert the building storey to a DataObject for the level proxy
            storey_display_value = self.cached_display_values.get(step_element.id(), [])
            self._current_storey_data_object = data_object_to_speckle(
                storey_display_value, step_element, []
            )

        children = self._convert_children(step_element)
        display_value = self.cached_display_values.get(step_element.id(), [])

        if display_value is not None:
            self.geometries_used += 1

        # Extract current storey name from DataObject if available
        current_storey_name = (
            self._current_storey_data_object.name
            if self._current_storey_data_object
            else None
        )

        if step_element.is_a("IfcProject"):
            result = project_to_speckle(step_element, children)
        elif step_element.is_a("IfcSpatialStructureElement"):
            result = spatial_element_to_speckle(
                display_value, step_element, children, current_storey_name
            )
        else:
            result = data_object_to_speckle(
                display_value, step_element, children, current_storey_name
            )
            # Associate non-spatial elements with current storey for level proxies
            if self._current_storey_data_object is not None and result.applicationId:
                self._level_proxy_manager.add_element_level_mapping(
                    self._current_storey_data_object, result.applicationId
                )

        # Restore previous storey context
        self._current_storey_data_object = previous_storey_data_object
        return result

    def _convert_children(self, step_element: entity_instance) -> list[Base]:
        return [
            self.convert_element(i)
            for i in get_children(step_element)
            if self._should_convert(i)
        ]

    @staticmethod
    def _should_convert(step_element: entity_instance) -> bool:
        # We only consider IfcRoot objects convertible
        # This is the super class for root level entities that have a GUID...
        # This will ignore some types like IfcGridAxis
        s = step_element.is_a("IfcRoot")
        if not s:
            print(
                f"Skipping #{step_element.id()} because it's type ({step_element.is_a()}) it not an IfcRoot"  # noqa: E501
            )
        return s

    def convert(self) -> Base:
        start = time.time()
        self.pre_process_geometry()
        print(f"Geometry conversion complete after {(time.time() - start) * 1000}ms")
        print(f"Created {self.geometries_count} geometries")

        start = time.time()
        root = self._convert_project_tree()
        print(f"Object tree conversion complete after {(time.time() - start) * 1000}ms")
        print(f"Used {self.geometries_used} geometries")
        return root

    def pre_process_geometry(self) -> None:
        iterator = create_geometry_iterator(self.ifc_file)
        if not iterator.initialize():
            raise SpeckleException(
                "geometry iterator failed to initialize for the given file"
            )
        self.geometries_count = 0
        while True:
            shape = cast(TriangulationElement, iterator.get())
            self.geometries_count += 1
            id = cast(int, shape.id)

            display_value = geometry_to_speckle(shape, self._render_material_manager)
            self.cached_display_values[id] = display_value

            if not iterator.next():
                break

    def _convert_project_tree(self) -> Base:
        projects = self.ifc_file.by_type("IfcProject", False)
        if len(projects) != 1:
            raise SpeckleException("Expected exactly one IfcProject in file")
        project = projects[0]

        tree = self.convert_element(project)
        tree["renderMaterialProxies"] = list(
            self._render_material_manager.render_material_proxies.values()
        )
        tree["levelProxies"] = list(self._level_proxy_manager.level_proxies.values())
        tree["version"] = 3

        return tree
