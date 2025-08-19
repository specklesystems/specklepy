from typing import Any

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_psets
from ifcopenshell.util.unit import get_full_unit_name, get_project_unit


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

        # Get the project unit for this unit type (with built-in caching)
        project_unit = get_project_unit(element.file, unit_type, use_cache=True)
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


def get_quantities(element: entity_instance) -> dict[str, object]:
    """
    Extract quantity takeoffs (QTOs) from an IFC element with unit information.
    """
    # Get basic quantities using existing utility
    quantities = get_psets(element, qtos_only=True, should_inherit=False)
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
                qty_entity = quantity_entities[qty_name]
                unit_info = _get_unit_info(element, qty_entity.is_a())

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

            enhanced_quantities[pset_name] = enhanced_pset

        except (KeyError, AttributeError):
            # If entity access fails, use original data as fallback
            enhanced_quantities[pset_name] = pset_data

    return enhanced_quantities
