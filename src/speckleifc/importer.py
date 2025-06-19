from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects import Base

from speckleifc.converter.data_object_converter import data_object_to_speckle
from speckleifc.converter.project_converter import project_to_speckle
from speckleifc.converter.spatial_element_converter import spatial_element_to_speckle
from speckleifc.ifc_geometry_processing import try_get_shape
from speckleifc.ifc_openshell_helpers import get_children
from speckleifc.root_object_builder import RootObjectBuilder


class ImportJob:
    def __init__(self, ifc_file: file):
        self._ifc_file = ifc_file
        self.builder = RootObjectBuilder()

    def convert_element(self, step_element: entity_instance) -> Base:
        children = self._convert_children(step_element)
        shape = try_get_shape(step_element)

        if step_element.is_a("IfcProject"):
            return project_to_speckle(step_element, children)
        elif step_element.is_a("IfcSpatialStructureElement"):
            return spatial_element_to_speckle(shape, step_element, children)
        else:
            return data_object_to_speckle(shape, step_element, children)

    def _convert_children(self, step_element: entity_instance) -> list[Base]:
        return [self.convert_element(i) for i in get_children(step_element)]

    ## OLD

    def convert(self) -> Base:

        root = self._convert_project_tree()

        return root

    def _convert_project_tree(self) -> Base:
        projects = self._ifc_file.by_type("IfcProject", False)
        if len(projects) != 1:
            raise SpeckleException("Expected exactly one IfcProject in file")
        project = projects[0]

        tree = self.convert_element(project)

        return tree
