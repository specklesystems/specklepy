from typing import Any

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_psets, get_type
from ifcopenshell.util.unit import get_full_unit_name, get_project_unit, get_unit_symbol


def extract_properties(element: entity_instance) -> dict[str, object]:
    properties: dict[str, object] = {
        "Attributes": _get_attributes(element),
        "Property Sets": _get_ifc_object_properties(element),
    }

    # Add quantities if they exist
    quantities = _get_quantities(element)
    if quantities:
        properties["Quantities"] = quantities

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


def _format_unit_name(unit_name: str) -> str:
    """
    Convert IFC unit names to user-friendly format.

    Args:
        unit_name: The raw IFC unit name (e.g., 'SQUARE_METRE')

    Returns:
        User-friendly unit name (e.g., 'Square metre')
    """
    if not unit_name:
        return ""

    # Convert underscore-separated words to space-separated and title case
    formatted = unit_name.replace("_", " ").lower()

    # Special cases for better formatting
    unit_replacements = {
        "metre": "metre",
        "meter": "meter",
        "square metre": "Square metre",
        "square meter": "Square meter",
        "cubic metre": "Cubic metre",
        "cubic meter": "Cubic meter",
        "kilogram": "Kilogram",
        "gram": "Gram",
        "second": "Second",
        "minute": "Minute",
        "hour": "Hour",
        "day": "Day",
    }

    # Apply replacements or default to title case
    return unit_replacements.get(formatted, formatted.title())


def _get_unit_info(element: entity_instance, quantity_type: str) -> dict[str, str]:
    """
    Get unit information for a given quantity type from the IFC project.

    Args:
        element: The IFC element to get the project context from
        quantity_type: The IFC quantity type
                      (e.g., 'IfcQuantityLength', 'IfcQuantityArea')

    Returns:
        Dict containing unit name and symbol, or empty dict if unit not found
    """
    try:
        # Map IFC quantity types to unit types
        unit_type_mapping = {
            "IfcQuantityLength": "LENGTHUNIT",
            "IfcQuantityArea": "AREAUNIT",
            "IfcQuantityVolume": "VOLUMEUNIT",
            "IfcQuantityCount": None,  # Count quantities typically have no units
            "IfcQuantityWeight": "MASSUNIT",
            "IfcQuantityTime": "TIMEUNIT",
        }

        unit_type = unit_type_mapping.get(quantity_type)
        if not unit_type:
            return {}

        # Get the project unit for this unit type
        project_unit = get_project_unit(element.file, unit_type)
        if not project_unit:
            return {}

        # Get unit name and symbol
        unit_name = get_full_unit_name(project_unit)
        unit_symbol = get_unit_symbol(project_unit)

        # Format the unit name to be user-friendly
        formatted_unit_name = _format_unit_name(unit_name)

        return {"units": formatted_unit_name, "unit_symbol": unit_symbol or ""}
    except Exception:
        # If anything fails, return empty dict to maintain robustness
        return {}


def _get_quantities(element: entity_instance) -> dict[str, object]:
    """
    Extract quantity takeoffs (QTOs) from an IFC element with unit information.
    """
    # Get basic quantities using existing utility
    quantities = get_psets(element, qtos_only=True)
    if not quantities:
        return {}

    # Enhance each QTO pset with unit information
    enhanced_quantities = {}

    for pset_name, pset_data in quantities.items():
        if not isinstance(pset_data, dict) or "id" not in pset_data:
            # Fallback for unexpected data structure
            enhanced_quantities[pset_name] = pset_data
            continue

        try:
            # Get the actual IfcElementQuantity entity
            pset_entity = element.file.by_id(pset_data["id"])
            if not pset_entity or not hasattr(pset_entity, "Quantities"):
                # Fallback if entity not found or invalid
                enhanced_quantities[pset_name] = pset_data
                continue

            # Transform quantities to include unit information
            enhanced_pset = {"id": pset_data["id"]}

            # Create mapping of quantity names to their IFC entities for unit lookup
            quantity_entities = {
                q.Name: q for q in pset_entity.Quantities if hasattr(q, "Name")
            }

            for qty_name, qty_value in pset_data.items():
                if qty_name == "id":
                    continue

                # Get the IFC quantity entity for unit information
                qty_entity = quantity_entities.get(qty_name)
                if qty_entity:
                    quantity_type = qty_entity.is_a()
                    unit_info = _get_unit_info(element, quantity_type)

                    if unit_info:
                        # Create structured quantity object with units
                        enhanced_pset[qty_name] = {
                            "name": qty_name,
                            "value": qty_value,
                            **unit_info,
                        }
                    else:
                        # No unit info available, keep as simple value with name
                        enhanced_pset[qty_name] = {"name": qty_name, "value": qty_value}
                else:
                    # Quantity entity not found, keep as simple value with name
                    enhanced_pset[qty_name] = {"name": qty_name, "value": qty_value}

            enhanced_quantities[pset_name] = enhanced_pset

        except Exception:
            # If anything fails for this pset, use original data
            enhanced_quantities[pset_name] = pset_data

    return enhanced_quantities
