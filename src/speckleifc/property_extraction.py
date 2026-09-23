import math
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

    ifc_type = get_type(element)
    if ifc_type is not None:
        properties["Element Type Property Sets"] = _get_ifc_element_type_properties(
            ifc_type,
        )
        properties["Element Type Attributes"] = _get_attributes(
            ifc_type,
        )

    # FEA-716: `IfcRelAssociatesMaterial`/`IfcRelAssociatesClassification` are data
    # associations (IfcRelAssociates*), not property sets, so _get_ifc_object_properties
    # (which only walks IfcRelDefinesByProperties) never sees them — hence Bram's "IFC
    # Material"/"Classification Uniformat" going missing. Surfaced here as ordinary
    # top-level properties, named and shaped to match what Revit's own IFC import
    # already calls them and how it groups their fields ("IFC Material" > Name (Color
    # when it has one); "Classification <system>" > Classification, Name, Reference) —
    # the exact grouped layout from the customer's screenshot, each a sub-dict rather
    # than one flattened string, consistent with how `Quantities` groups
    # `Qto_*BaseQuantities` fields instead of flattening those too. So a model
    # round-tripped through Revit and one round-tripped straight through this importer
    # read the same on this data, and it doesn't need a bespoke bundle-spec
    # relationship: the OBJECT_HAS_MATERIAL/NODE_HAS_MATERIAL edges other producers
    # (AutoCAD/SketchUp via the managed pipeline) already use are placement-painting
    # appearance with defined fill precedence over geometry — a different concept from
    # this data-level assignment, and Revit's own producer doesn't use them for its
    # data material either.
    material_name = extract_material_name(element)
    if material_name:
        properties["IFC Material"] = {"Name": material_name}

    for system_name, value in _get_classifications(element, ifc_type).items():
        properties[f"Classification {system_name}"] = value

    return properties


def extract_material_name(element: entity_instance) -> str | None:
    """The element's IFC data-material assignment (``IfcRelAssociatesMaterial``),
    as a single display name — FEA-716. This is distinct from render/visual
    material (``IfcSurfaceStyle`` → ``MaterialManager``/``HAS_MATERIAL``): it's the
    "IFC Material" parameter authoring tools show (e.g. Revit), sourced from the
    material *data* relationship, not geometry styling. Occurrence-level
    association wins; falls back to the element type's when the occurrence carries
    none, matching how psets/qtos already prefer the occurrence.
    """
    name = _material_name_from_associations(element)
    if name is not None:
        return name
    ifc_type = get_type(element)
    if ifc_type is not None:
        return _material_name_from_associations(ifc_type)
    return None


def _material_name_from_associations(element: entity_instance) -> str | None:
    for rel in getattr(element, "HasAssociations", None) or []:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        name = _material_select_name(rel.RelatingMaterial)
        if name:
            return name
    return None


def _material_select_name(material: entity_instance | None) -> str | None:
    """Resolve any ``IfcMaterialSelect`` variant to a single display name. Layered
    and constituent materials (walls, slabs, ...) commonly carry more than one
    constituent material; those are joined so nothing is silently dropped, mirroring
    how Revit surfaces a compound structure's "IFC Material" as one delimited value.
    """
    if material is None:
        return None

    if material.is_a("IfcMaterial"):
        return material.Name or None

    if material.is_a("IfcMaterialList"):
        names = [m.Name for m in material.Materials or [] if m.Name]
        return _join_names(names)

    if material.is_a("IfcMaterialConstituentSet"):
        names = [
            c.Material.Name
            for c in material.MaterialConstituents or []
            if c.Material is not None and c.Material.Name
        ]
        return _join_names(names)

    if material.is_a("IfcMaterialLayerSetUsage"):
        return _material_select_name(material.ForLayerSet)

    if material.is_a("IfcMaterialLayerSet"):
        names = [
            layer.Material.Name
            for layer in material.MaterialLayers or []
            if layer.Material is not None and layer.Material.Name
        ]
        return _join_names(names)

    if material.is_a("IfcMaterialProfileSetUsage"):
        return _material_select_name(material.ForProfileSet)

    if material.is_a("IfcMaterialProfileSet"):
        names = [
            profile.Material.Name
            for profile in material.MaterialProfiles or []
            if profile.Material is not None and profile.Material.Name
        ]
        return _join_names(names)

    return None


def _join_names(names: list[str]) -> str | None:
    # de-dupe while preserving order — a uniform layer set otherwise repeats itself
    seen: dict[str, None] = dict.fromkeys(names)
    return "; ".join(seen) or None


def _get_classifications(
    element: entity_instance, ifc_type: entity_instance | None
) -> dict[str, dict[str, str]]:
    """``IfcRelAssociatesClassification`` → ``{system name: {Classification, Name,
    Reference}}``, e.g. "Classification Uniformat" → ``{"Classification":
    "Uniformat", "Name": "Roof Construction", "Reference": "B1020"}`` (FEA-716) — a
    sub-dict per system, grouped and labelled the way Revit's own IFC import already
    shows it, rather than one flattened string. Occurrence associations win over the
    type's, per system, matching how psets/qtos already prefer the occurrence.

    Kept as a property rather than a bundle relationship: the bundle spec's node/rel
    catalogue has no CLASSIFICATION node kind today (only
    MATERIAL/COLOR/LEVEL/CONTAINER), so there's no relationship primitive to model
    this on — adding one is a spec-level change (ADR territory), out of scope here.
    """
    result: dict[str, dict[str, str]] = {}
    if ifc_type is not None:
        result.update(_classifications_from_associations(ifc_type))
    result.update(_classifications_from_associations(element))
    return result


def _classifications_from_associations(
    element: entity_instance,
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for rel in getattr(element, "HasAssociations", None) or []:
        if not rel.is_a("IfcRelAssociatesClassification"):
            continue
        entry = _classification_entry(rel.RelatingClassification)
        if entry is not None:
            system_name, value = entry
            result[system_name] = value
    return result


def _classification_entry(
    reference: entity_instance | None,
) -> tuple[str, dict[str, str]] | None:
    if reference is None:
        return None

    if reference.is_a("IfcClassificationReference"):
        source = getattr(reference, "ReferencedSource", None)
        system_name = str(
            (getattr(source, "Name", None) if source else None)
            or (reference.Name or "Classification")
        )
        identification = getattr(reference, "Identification", None) or getattr(
            reference, "ItemReference", None
        )
        value: dict[str, str] = {"Classification": system_name}
        if reference.Name:
            value["Name"] = str(reference.Name)
        if identification:
            value["Reference"] = str(identification)
        return (system_name, value) if len(value) > 1 else None

    if reference.is_a("IfcClassification"):
        if not reference.Name:
            return None
        name = str(reference.Name)
        return (name, {"Classification": name})

    return None


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

            # Server does not consider `NaN` valid json
            if math.isnan(value):
                value = None

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
