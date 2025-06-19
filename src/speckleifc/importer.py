from typing import cast

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file
from ifcopenshell.ifcopenshell_wrapper import TriangulationElement
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects import Base
from specklepy.objects.models.collections.collection import Collection

from speckleifc.converter.data_object_converter import data_object_to_speckle
from speckleifc.ifc_geometry_processing import create_geometry_iterator
from speckleifc.root_object_builder import RootObjectBuilder


class ImportJob:

    def __init__(self, ifc_file: file):
        self._ifc_file = ifc_file
        self.builder = RootObjectBuilder()

    def convert(self) -> Collection:
        self._convert_spatial_elements()

        self._convert_geometry()

        root = Collection(name="root collection")  # todo: replace with project
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
            self.builder.include_shape(converted, shape)

            if not geometry_iterator.next():
                break

    def _convert_spatial_elements(self) -> None:
        spatial_elements = self._ifc_file.by_type("IfcSpatialElement")

        for element in spatial_elements:
            element

    @staticmethod
    def convert_geometry_element(
        geometry_element: TriangulationElement, step_element: entity_instance
    ) -> Base:
        # step_entity = ifc_model.by_id(geometry_element.id())
        return data_object_to_speckle(geometry_element, step_element)
