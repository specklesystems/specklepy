from collections.abc import Iterable
from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from ifcopenshell.ifcopenshell_wrapper import TriangulationElement
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects import Base
from specklepy.objects.models.collections.collection import Collection

from speckleifc.converter.data_object_converter import data_object_to_speckle
from speckleifc.converter.project_converter import project_to_speckle
from speckleifc.converter.spatial_element_converter import spatial_element_to_speckle
from speckleifc.ifc_geometry_processing import create_geometry_iterator
from speckleifc.ifc_openshell_helpers import get_aggregates
from speckleifc.root_object_builder import RootObjectBuilder


class ImportJob:
    def __init__(self, ifc_file: file):
        self._ifc_file = ifc_file
        self.builder = RootObjectBuilder()

    def convert(self) -> Collection:
        # we're doing a bit of a hybrid approach to traversing the IFC graph.
        # First we convert the aggregates graph of spatial elements using a depth first
        # traversal of the aggregate relationships, starting from the project.
        # This will convert the IfcProject, IfcSite, IfcBuilding, IfcBuildingStorey etc..
        # Note that some of these, like IfcSite may still have geometry...
        #
        # This DFS approach is similar to how the v2 and v3 web-ifc based importers worked
        # But here, is only doing Spatial elements, not walls
        root = self._convert_project_tree()

        # Then, geometry is converted using the geometry iterator, this is efficient
        # but returns objects in a non-reliable order, so we use the RootObjectBuilder
        # to differ building the rest of the Speckle objects tree
        self._convert_geometry()
        self.builder.build_commit_object(root)

        return root

    def _convert_geometry(self) -> None:
        geometry_iterator = create_geometry_iterator(self._ifc_file)

        if not geometry_iterator.initialize():
            raise SpeckleException("Iterator failed to initialize")

        while True:
            shape = geometry_iterator.get()
            assert isinstance(shape, TriangulationElement)

            step_id = cast(int, shape.id)
            step_element = self._ifc_file.by_id(step_id)

            converted = self.convert_geometry_element(shape, step_element)
            self.builder.include_object(converted, step_element, shape)

            if not geometry_iterator.next():
                break

    def _convert_spatial_elements_tree(
        self, step_element: entity_instance
    ) -> Collection:

        children = self._convert_aggregates(step_element)

        result = spatial_element_to_speckle(step_element, children)

        # Include object in the converted dictionary,
        # but no need to set relationships, since we're correctly handling those already
        # the the spatial elements traversed here
        self.builder.converted[step_element.id()] = result
        return result

    def _convert_project_tree(self) -> Collection:
        projects = self._ifc_file.by_type("IfcProject", False)
        if len(projects) != 1:
            raise SpeckleException("Expected exactly one IfcProject in file")
        project = projects[0]

        children = self._convert_aggregates(project)
        result = project_to_speckle(project, children)

        self.builder.converted[project.id()] = result

        return result

    def _convert_aggregates(self, step_element: entity_instance) -> list[Base]:
        return [
            self._convert_spatial_elements_tree(i) for i in get_aggregates(step_element)
        ]

    @staticmethod
    def convert_geometry_element(
        geometry_element: TriangulationElement, step_element: entity_instance
    ) -> Base:
        # step_entity = ifc_model.by_id(geometry_element.id())
        return data_object_to_speckle(geometry_element, step_element)
