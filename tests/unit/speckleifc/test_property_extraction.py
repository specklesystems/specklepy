"""FEA-716 — IFC data-material and classification associations.

Unit-level coverage for the ``property_extraction`` helpers added for FEA-716:
``extract_material_name`` (resolves ``IfcRelAssociatesMaterial`` across every
``IfcMaterialSelect`` variant into a single display name) and ``_get_classifications``
(``IfcRelAssociatesClassification`` → one property per classification system).

Both are surfaced as ordinary top-level properties — "IFC Material" and
"Classification <system>" — named and *shaped* (sub-dicts: Name for material;
Classification/Name/Reference for classification) to match what Revit's own IFC
import already calls and groups them, per Jonathon's follow-up screenshot, rather
than a bespoke bundle relationship: see the comment in ``extract_properties`` for
why.

Exercised against lightweight fakes that duck-type just the ifcopenshell
``entity_instance`` surface these helpers touch (``is_a`` plus the handful of
named attributes), rather than a real IFC fixture — the logic under test is the
IFC-select resolution, not the parser, and a fake keeps each case legible and
independent of a checked-in STEP file's exact authoring.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

from speckleifc.property_extraction import (  # noqa: E402
    _get_classifications,
    extract_material_name,
    extract_properties,
)


class FakeEntity:
    """Duck-types the bits of ``ifcopenshell.entity_instance`` these helpers use."""

    def __init__(self, ifc_class: str, **attrs: Any) -> None:
        self._ifc_class = ifc_class
        self.__dict__.update(attrs)

    def is_a(self, ifc_class: str | None = None) -> Any:
        if ifc_class is None:
            return self._ifc_class
        return self._ifc_class == ifc_class

    def __getattr__(self, name: str) -> Any:
        # ifcopenshell entities return None for absent optional attributes rather
        # than raising, and the helpers rely on that.
        return None


def material(name: str) -> FakeEntity:
    return FakeEntity("IfcMaterial", Name=name)


def rel_associates_material(relating_material: FakeEntity) -> FakeEntity:
    return FakeEntity("IfcRelAssociatesMaterial", RelatingMaterial=relating_material)


def element_with(
    *,
    associations: list[FakeEntity] | None = None,
    global_id: str = "0",
    is_a: str = "IfcWall",
) -> FakeEntity:
    return FakeEntity(
        is_a,
        HasAssociations=associations or [],
        IsDefinedBy=[],
        HasPropertySets=[],
        GlobalId=global_id,
        get_info=lambda *a, **k: {},
    )


# ── material name resolution ────────────────────────────────────────────────


def test_single_material_resolves_by_name():
    element = element_with(associations=[rel_associates_material(material("Concrete"))])
    assert extract_material_name(element) == "Concrete"


def test_material_list_joins_names():
    ml = FakeEntity("IfcMaterialList", Materials=[material("Steel"), material("Glass")])
    element = element_with(associations=[rel_associates_material(ml)])
    assert extract_material_name(element) == "Steel; Glass"


def test_material_constituent_set_joins_unique_constituent_names():
    constituents = [
        FakeEntity("IfcMaterialConstituent", Material=material("Timber")),
        FakeEntity("IfcMaterialConstituent", Material=material("Insulation")),
        FakeEntity("IfcMaterialConstituent", Material=material("Timber")),  # dup
    ]
    cset = FakeEntity("IfcMaterialConstituentSet", MaterialConstituents=constituents)
    element = element_with(associations=[rel_associates_material(cset)])
    assert extract_material_name(element) == "Timber; Insulation"


def test_material_layer_set_usage_resolves_through_layer_set():
    layers = [
        FakeEntity("IfcMaterialLayer", Material=material("Brick")),
        FakeEntity("IfcMaterialLayer", Material=material("Cavity")),
    ]
    layer_set = FakeEntity("IfcMaterialLayerSet", MaterialLayers=layers)
    usage = FakeEntity("IfcMaterialLayerSetUsage", ForLayerSet=layer_set)
    element = element_with(associations=[rel_associates_material(usage)])
    assert extract_material_name(element) == "Brick; Cavity"


def test_material_profile_set_usage_resolves_through_profile_set():
    profiles = [FakeEntity("IfcMaterialProfile", Material=material("Steel"))]
    profile_set = FakeEntity("IfcMaterialProfileSet", MaterialProfiles=profiles)
    usage = FakeEntity("IfcMaterialProfileSetUsage", ForProfileSet=profile_set)
    element = element_with(associations=[rel_associates_material(usage)])
    assert extract_material_name(element) == "Steel"


def test_no_association_returns_none(monkeypatch):
    element = element_with(associations=[])
    monkeypatch.setattr("speckleifc.property_extraction.get_type", lambda e: None)
    assert extract_material_name(element) is None


def test_occurrence_material_wins_over_type(monkeypatch):
    element = element_with(
        associations=[rel_associates_material(material("Occurrence Concrete"))]
    )
    type_element = element_with(
        associations=[rel_associates_material(material("Type Concrete"))],
        is_a="IfcWallType",
    )
    monkeypatch.setattr(
        "speckleifc.property_extraction.get_type", lambda e: type_element
    )
    assert extract_material_name(element) == "Occurrence Concrete"


def test_falls_back_to_type_material_when_occurrence_has_none(monkeypatch):
    element = element_with(associations=[])
    type_element = element_with(
        associations=[rel_associates_material(material("Type Concrete"))],
        is_a="IfcWallType",
    )
    monkeypatch.setattr(
        "speckleifc.property_extraction.get_type", lambda e: type_element
    )
    assert extract_material_name(element) == "Type Concrete"


def test_extract_properties_surfaces_ifc_material(monkeypatch):
    element = element_with(associations=[rel_associates_material(material("Concrete"))])
    monkeypatch.setattr("speckleifc.property_extraction.get_type", lambda e: None)

    properties = extract_properties(element)

    assert properties["IFC Material"] == {"Name": "Concrete"}


def test_extract_properties_omits_ifc_material_when_none(monkeypatch):
    element = element_with(associations=[])
    monkeypatch.setattr("speckleifc.property_extraction.get_type", lambda e: None)

    properties = extract_properties(element)

    assert "IFC Material" not in properties


# ── classification extraction ───────────────────────────────────────────────


def classification_reference(
    *, identification: str | None, name: str | None, system: str | None
) -> FakeEntity:
    source = FakeEntity("IfcClassification", Name=system) if system else None
    return FakeEntity(
        "IfcClassificationReference",
        Identification=identification,
        Name=name,
        ReferencedSource=source,
    )


def rel_associates_classification(reference: FakeEntity) -> FakeEntity:
    return FakeEntity(
        "IfcRelAssociatesClassification", RelatingClassification=reference
    )


def test_classification_reference_keyed_by_source_system_name():
    reference = classification_reference(
        identification="B1020", name="Roof Construction", system="Uniformat"
    )
    element = element_with(associations=[rel_associates_classification(reference)])
    assert _get_classifications(element, None) == {
        "Uniformat": {
            "Classification": "Uniformat",
            "Name": "Roof Construction",
            "Reference": "B1020",
        }
    }


def test_classification_reference_without_source_falls_back_to_reference_name():
    reference = classification_reference(
        identification="X-1", name="Custom System", system=None
    )
    element = element_with(associations=[rel_associates_classification(reference)])
    assert _get_classifications(element, None) == {
        "Custom System": {
            "Classification": "Custom System",
            "Name": "Custom System",
            "Reference": "X-1",
        }
    }


def test_classification_reference_with_only_identification():
    reference = classification_reference(
        identification="B1020", name=None, system="Uniformat"
    )
    element = element_with(associations=[rel_associates_classification(reference)])
    assert _get_classifications(element, None) == {
        "Uniformat": {"Classification": "Uniformat", "Reference": "B1020"}
    }


def test_direct_classification_association():
    reference = FakeEntity("IfcClassification", Name="Uniclass")
    element = element_with(associations=[rel_associates_classification(reference)])
    assert _get_classifications(element, None) == {
        "Uniclass": {"Classification": "Uniclass"}
    }


def test_classification_reference_with_neither_name_nor_identification_is_dropped():
    reference = classification_reference(
        identification=None, name=None, system="Uniformat"
    )
    element = element_with(associations=[rel_associates_classification(reference)])
    assert _get_classifications(element, None) == {}


def test_no_classification_associations_yields_empty_dict():
    element = element_with(associations=[])
    assert _get_classifications(element, None) == {}


def test_occurrence_classification_wins_over_type_per_system():
    occurrence_ref = classification_reference(
        identification="B1020", name="Roof", system="Uniformat"
    )
    element = element_with(associations=[rel_associates_classification(occurrence_ref)])
    type_ref_same_system = classification_reference(
        identification="B9999", name="Type default", system="Uniformat"
    )
    type_ref_other_system = classification_reference(
        identification="12-34", name="Roofs", system="Uniclass"
    )
    type_element = element_with(
        associations=[
            rel_associates_classification(type_ref_same_system),
            rel_associates_classification(type_ref_other_system),
        ],
        is_a="IfcRoofType",
    )

    result = _get_classifications(element, type_element)

    assert result == {
        # occurrence override, not the type's B9999/"Type default"
        "Uniformat": {
            "Classification": "Uniformat",
            "Name": "Roof",
            "Reference": "B1020",
        },
        # type-only system still comes through
        "Uniclass": {
            "Classification": "Uniclass",
            "Name": "Roofs",
            "Reference": "12-34",
        },
    }


def test_extract_properties_surfaces_classification_by_system_name(monkeypatch):
    reference = classification_reference(
        identification="B1020", name="Roof Construction", system="Uniformat"
    )
    element = element_with(associations=[rel_associates_classification(reference)])
    monkeypatch.setattr("speckleifc.property_extraction.get_type", lambda e: None)

    properties = extract_properties(element)

    assert properties["Classification Uniformat"] == {
        "Classification": "Uniformat",
        "Name": "Roof Construction",
        "Reference": "B1020",
    }
