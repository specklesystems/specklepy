from typing import Any

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_type


def extract_properties(element: entity_instance) -> dict[str, object]:
    properties: dict[str, object] = {
        "Attributes": _get_attributes(element),
        "Property Sets": _get_ifc_object_properties(element),
    }

    # Add building storey information if element is contained in a storey
    if storey_name := _get_containing_storey(element):
        properties["Building Storey"] = storey_name

    if (ifc_type := get_type(element)) is not None:
        properties["Element Type Property Sets"] = _get_ifc_element_type_properties(
            ifc_type,
        )
        properties["Element Type Attributes"] = _get_attributes(
            ifc_type,
        )

    return properties


def _get_attributes(element: entity_instance) -> dict[str, object]:
    return element.get_info(True, False, scalar_only=True)


def _get_ifc_element_type_properties(element: entity_instance) -> dict[str, object]:
    result: dict[str, object] = {}
    for definition in element.HasPropertySets or []:
        if not definition.is_a("IfcPropertySet"):
            continue

        result[definition.Name] = _get_properties(definition.HasProperties)
    return result


def _get_ifc_object_properties(element: entity_instance) -> dict[str, object]:
    result: dict[str, object] = {}

    for rel in getattr(element, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue

        definition: entity_instance | None = rel.RelatingPropertyDefinition
        if not definition:
            continue

        if not definition.is_a("IfcPropertySet"):
            continue

        set_name = definition.Name
        properties = _get_properties(definition.HasProperties)

        if properties:
            result[set_name] = properties

    return result


def _get_properties(properties: entity_instance) -> dict[str, Any]:
    """
    There already exists a canonical way to get properties
    `ifcopenshell.util.element.get_properties` but it's very verbose
    and we don't want to bloat our selves with supporting complex property types

    This is a slimmed down version, only supporting a couple of property types
    """
    result: dict[str, Any] = {}

    for prop in properties:
        name = prop.Name
        if prop.is_a("IfcPropertySingleValue"):
            val = prop.NominalValue
            if val is not None:
                result[name] = val.wrappedValue if hasattr(val, "wrappedValue") else val
        elif prop.is_a("IfcPropertyListValue"):
            values = getattr(prop, "ListValues", None)
            if values:
                result[name] = [
                    v.wrappedValue if hasattr(v, "wrappedValue") else v for v in values
                ]
        elif prop.is_a("IfcPropertyEnumeratedValue"):
            values = getattr(prop, "EnumerationValues", None)
            if values:
                result[name] = [
                    v.wrappedValue if hasattr(v, "wrappedValue") else v for v in values
                ]

        # elif prop.is_a("IfcPropertyTableValue"):
        #     properties[name] = #not sure if we want to support these...
    return result


def _get_containing_storey(element: entity_instance) -> str | None:
    """
    Find the containing IfcBuildingStorey for an element by traversing up
    the spatial hierarchy. Returns the storey name if found, None otherwise.
    """
    # Check if element has spatial containment relationships
    containment_rels = getattr(element, "ContainedInStructure", None)
    if not containment_rels:
        return None

    # Traverse the spatial containment relationships
    for rel in containment_rels:
        if not rel.is_a("IfcRelContainedInSpatialStructure"):
            continue

        relating_structure = getattr(rel, "RelatingStructure", None)
        if not relating_structure:
            continue

        # Check if this structure is a building storey
        if relating_structure.is_a("IfcBuildingStorey"):
            return (
                relating_structure.Name
                or relating_structure.LongName
                or relating_structure.GlobalId
            )

        # If not, recursively check the parent structure
        parent_storey = _get_containing_storey(relating_structure)
        if parent_storey:
            return parent_storey

    return None
