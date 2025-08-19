from typing import Any

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.unit import get_full_unit_name, get_project_unit


def _format_unit_name(unit_name: str) -> str:
    """
    Convert IFC unit names to user-friendly format.
    """
    if not unit_name:
        return ""

    # Convert underscore-separated words to space-separated and title case
    return unit_name.replace("_", " ").title()


def _get_unit_info(element: entity_instance, quantity) -> dict[str, str]:
    """Get unit information for a quantity."""
    try:
        if hasattr(quantity, 'Unit') and quantity.Unit:
            # Quantity has its own unit
            try:
                unit_name = get_full_unit_name(quantity.Unit)
                formatted_unit_name = _format_unit_name(unit_name)
                return {"units": formatted_unit_name}
            except:
                return {"units": str(quantity.Unit)}
        else:
            # Fall back to project unit based on quantity type
            unit_mapping = {
                "IfcQuantityLength": "LENGTHUNIT",
                "IfcQuantityArea": "AREAUNIT", 
                "IfcQuantityVolume": "VOLUMEUNIT",
                "IfcQuantityCount": None,  # Count quantities typically have no units
                "IfcQuantityWeight": "MASSUNIT",
                "IfcQuantityTime": "TIMEUNIT"
            }
            
            quantity_type = quantity.is_a()
            unit_type = unit_mapping.get(quantity_type)
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


def _get_quantities(quantities: list[entity_instance], element: entity_instance) -> dict[str, Any]:
    """Extract quantity values from IfcPhysicalQuantity entities."""
    results = {}
    for quantity in quantities or []:
        quantity_name = quantity.Name
        if quantity.is_a("IfcPhysicalSimpleQuantity"):
            # Get the quantity value (3rd attribute for simple quantities)
            value = getattr(quantity, quantity.attribute_name(3))
            unit_info = _get_unit_info(element, quantity)
            
            if unit_info:
                # Create structured quantity object with units
                results[quantity_name] = {
                    "name": quantity_name,
                    "value": value,
                    **unit_info,
                }
            else:
                # No unit info available, keep as simple value with name
                results[quantity_name] = {"name": quantity_name, "value": value}
            
        elif quantity.is_a("IfcPhysicalComplexQuantity"):
            # Handle complex quantities
            data = {k: v for k, v in quantity.get_info().items() if v is not None and k != "Name"}
            data["properties"] = _get_quantities(quantity.HasQuantities, element)
            del data["HasQuantities"]
            results[quantity_name] = data
    return results


def get_quantities(element: entity_instance) -> dict[str, object]:
    """
    Extract quantity takeoffs (QTOs) from an IFC element with unit information.
    """
    qtos = {}
    
    # Handle elements with IsDefinedBy relationship
    if hasattr(element, "IsDefinedBy") and element.IsDefinedBy:
        for relationship in element.IsDefinedBy:
            if relationship.is_a("IfcRelDefinesByProperties"):
                definition = relationship.RelatingPropertyDefinition
                if definition.is_a("IfcElementQuantity"):
                    try:
                        quantities_data = _get_quantities(definition.Quantities, element)
                        quantities_data["id"] = definition.id()
                        qtos[definition.Name] = quantities_data
                    except (KeyError, AttributeError):
                        # If entity access fails, skip this quantity set
                        continue
    
    return qtos