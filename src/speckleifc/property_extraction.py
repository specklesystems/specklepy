from typing import Any

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_psets, get_type
from ifcopenshell.util.unit import get_full_unit_name, get_project_unit

# Global cache for project units per IFC file
_file_project_units_cache: dict[int, dict[str, Any]] = {}

# Cache for unit information by quantity field name per file
_quantity_field_units_cache: dict[int, dict[str, dict[str, str]]] = {}


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


def _get_cached_project_unit(element: entity_instance, unit_type: str):
    """
    Get project unit with caching per file.

    Args:
        element: The IFC element to get the project context from
        unit_type: The unit type (e.g., 'LENGTHUNIT', 'AREAUNIT')

    Returns:
        Project unit object or None if not found
    """
    file_id = id(element.file)  # Use file object ID as cache key

    # Initialize cache for this file if needed
    if file_id not in _file_project_units_cache:
        _file_project_units_cache[file_id] = {}

    file_cache = _file_project_units_cache[file_id]

    # Check if we already cached this unit type for this file
    if unit_type in file_cache:
        return file_cache[unit_type]

    # Not cached - get project unit and cache it
    try:
        project_unit = get_project_unit(element.file, unit_type)
        file_cache[unit_type] = project_unit
        return project_unit
    except Exception:
        # Cache None for failed lookups to avoid repeated failures
        file_cache[unit_type] = None
        return None


def _get_cached_field_unit_info(element: entity_instance, qty_entity) -> dict[str, str]:
    """
    Get unit info for quantity field with caching by quantity type.

    Args:
        element: The IFC element to get the project context from
        qty_entity: The IFC quantity entity

    Returns:
        Dict containing unit name, or empty dict if unit not found
    """
    file_id = id(element.file)
    quantity_type = qty_entity.is_a()

    # Initialize file cache if needed
    if file_id not in _quantity_field_units_cache:
        _quantity_field_units_cache[file_id] = {}

    field_cache = _quantity_field_units_cache[file_id]

    # Check if we already cached this quantity type for this file
    if quantity_type in field_cache:
        return field_cache[quantity_type]

    # Not cached - compute unit info and cache it
    unit_info = _get_unit_info(element, quantity_type)
    field_cache[quantity_type] = unit_info
    return unit_info


def _format_unit_name(unit_name: str) -> str:
    """
    Convert IFC unit names to user-friendly format.
    """
    if not unit_name:
        return ""

    # Convert underscore-separated words to space-separated and title case
    return unit_name.replace("_", " ").title()


def _get_unit_info(element: entity_instance, quantity_type: str) -> dict[str, str]:
    """
    Get unit information for a given quantity type from the IFC project.

    Args:
        element: The IFC element to get the project context from
        quantity_type: The IFC quantity type
                      (e.g., 'IfcQuantityLength', 'IfcQuantityArea')

    Returns:
        Dict containing unit name, or empty dict if unit not found
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

        # Get the project unit for this unit type (cached)
        project_unit = _get_cached_project_unit(element, unit_type)
        if not project_unit:
            return {}

        # Get unit name
        unit_name = get_full_unit_name(project_unit)

        # Format the unit name to be user-friendly
        formatted_unit_name = _format_unit_name(unit_name)

        return {"units": formatted_unit_name}
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
                    unit_info = _get_cached_field_unit_info(element, qty_entity)

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
