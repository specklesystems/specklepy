from typing import Any, Tuple

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.util.element import get_type
from ifcopenshell.util.unit import get_full_unit_name, get_project_unit

UNIT_MAPPING = {
    "IfcQuantityLength": "LENGTHUNIT",
    "IfcQuantityArea": "AREAUNIT",
    "IfcQuantityVolume": "VOLUMEUNIT",
    "IfcQuantityCount": None,  # Count quantities have no units
    "IfcQuantityWeight": "MASSUNIT",
    "IfcQuantityTime": "TIMEUNIT",
}


def extract_properties(element: entity_instance) -> dict[str, object]:
    (psets, qtos) = _get_ifc_object_properties(element)

    properties: dict[str, object] = {
        "Attributes": _get_attributes(element),
        "Property Sets": psets,
    }

    if qtos:
        properties["Quantities"] = qtos

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


def _get_ifc_object_properties(
    element: entity_instance,
) -> Tuple[dict[str, object], dict[str, object]]:
    psets: dict[str, object] = {}
    qtos: dict[str, object] = {}

    for rel in getattr(element, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue

        definition: entity_instance | None = rel.RelatingPropertyDefinition
        if not definition:
            continue

        try:
            if definition.is_a("IfcPropertySet"):
                set_name = definition.Name
                properties = _get_properties(definition.HasProperties)

                if properties:
                    psets[set_name] = properties

            elif definition.is_a("IfcElementQuantity"):
                quantities_data = _get_quantities(definition.Quantities, element)
                if not quantities_data:
                    continue
                quantities_data["id"] = definition.id()
                qtos[definition.Name] = quantities_data

        except (KeyError, AttributeError):
            # If entity access fails, skip this quantity set
            print(f"Skipping {definition}")
            continue

    return (psets, qtos)


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


def _get_quantities(
    quantities: list[entity_instance], element: entity_instance
) -> dict[str, Any]:
    """Extract quantity values from IfcPhysicalQuantity entities."""
    results: dict[str, Any] = {}
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
            data = {
                k: v
                for k, v in quantity.get_info().items()
                if v is not None and k != "Name"
            }
            data["properties"] = _get_quantities(quantity.HasQuantities, element)
            del data["HasQuantities"]
            results[quantity_name] = data
    return results


def _get_unit_info(
    element: entity_instance, quantity: entity_instance
) -> dict[str, str]:
    """Get unit information for a quantity."""
    # Early return for count quantities - they don't have units
    quantity_type = quantity.is_a()
    if quantity_type == "IfcQuantityCount":
        return {}

    unit = getattr(element, "Unit", None)
    if unit:
        # Quantity has its own unit
        unit_name = get_full_unit_name(unit)
        formatted_unit_name = unit_name.replace("_", " ").title() if unit_name else ""
        return {"units": formatted_unit_name}

    else:
        # Fall back to project unit based on quantity type
        unit_type = UNIT_MAPPING.get(quantity_type)
        if not unit_type:
            return {}

        # Get the project unit for this unit type
        project_unit = get_project_unit(element.file, unit_type, use_cache=True)
        if not project_unit:
            return {}

        # Get unit name and format
        unit_name = get_full_unit_name(project_unit)
        formatted_unit_name = unit_name.replace("_", " ").title() if unit_name else ""

        return {"units": formatted_unit_name}
