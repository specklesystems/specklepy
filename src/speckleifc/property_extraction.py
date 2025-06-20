from typing import Any

from ifcopenshell.entity_instance import entity_instance


def extract_properties(element: entity_instance) -> dict[str, object]:
    result: dict[str, object] = {}

    for rel in getattr(element, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue

        prop_set = rel.RelatingPropertyDefinition
        if not prop_set.is_a("IfcPropertySet"):
            continue

        set_name = prop_set.Name
        properties: dict[str, Any] = {}

        for prop in prop_set.HasProperties:
            name = prop.Name

            if prop.is_a("IfcPropertySingleValue"):
                val = prop.NominalValue
                if val is not None:
                    properties[name] = (
                        val.wrappedValue if hasattr(val, "wrappedValue") else val
                    )
            elif prop.is_a("IfcPropertyListValue"):
                values = getattr(prop, "ListValues", None)
                if values:
                    properties[name] = [
                        v.wrappedValue if hasattr(v, "wrappedValue") else v
                        for v in values
                    ]
            elif prop.is_a("IfcPropertyEnumeratedValue"):
                values = getattr(prop, "EnumerationValues", None)
                if values:
                    properties[name] = [
                        v.wrappedValue if hasattr(v, "wrappedValue") else v
                        for v in values
                    ]

            # elif prop.is_a("IfcPropertyTableValue"):
            #     properties[name] = #not sure if we want to support these...

        if properties:
            result[set_name] = properties

    return result
