"""Tests for the EAV property extraction (behaviour-parity with the C# port)."""

from __future__ import annotations

from specklepy.bundle.eav_extraction import (
    DEFAULT_EXCLUDED_TOP_LEVEL,
    MAX_DEPTH,
    REVIT_EXCLUDED_TOP_LEVEL,
    ROOT_SCALAR_FIELDS,
    EavRow,
    flatten_object_properties,
    flatten_properties,
    flatten_subtree,
    produces_rows,
)


def _by_path(rows: list[EavRow]) -> dict[str, EavRow]:
    return {r.path: r for r in rows}


# ───────────────────────────── nested dicts ────────────────────────────────


def test_nested_dict_dotted_paths():
    props = {
        "Attributes": {"GlobalId": "abc"},
        "Property Sets": {"Pset_WallCommon": {"IsExternal": True}},
    }
    rows = flatten_properties("obj1", props)
    paths = _by_path(rows)

    assert "properties.Attributes.GlobalId" in paths
    assert "properties.Property Sets.Pset_WallCommon.IsExternal" in paths
    assert paths["properties.Attributes.GlobalId"].object_id == "obj1"


def test_deeply_nested_paths_joined_with_dots():
    props = {"a": {"b": {"c": {"d": 5}}}}
    rows = flatten_properties("o", props)
    assert _by_path(rows)["properties.a.b.c.d"].value_num == 5.0


# ───────────────────────────── typing ──────────────────────────────────────


def test_number_boolean_string_typing():
    props = {"num": 42, "flt": 3.5, "flag": True, "text": "hello"}
    rows = _by_path(flatten_properties("o", props))

    assert rows["properties.num"].type == "number"
    assert rows["properties.num"].value_num == 42.0
    assert rows["properties.num"].value_text == "42"

    assert rows["properties.flt"].type == "number"
    assert rows["properties.flt"].value_num == 3.5

    assert rows["properties.flag"].type == "boolean"
    assert rows["properties.flag"].value_num is None
    assert rows["properties.flag"].value_text == "true"

    assert rows["properties.text"].type == "string"
    assert rows["properties.text"].value_num is None
    assert rows["properties.text"].value_text == "hello"


def test_integral_float_text_drops_trailing_zero():
    # JS String(1.0) === "1" / C# "R" format (EavExtraction.cs:790).
    rows = _by_path(flatten_properties("o", {"x": 1.0}))
    assert rows["properties.x"].value_text == "1"
    assert rows["properties.x"].value_num == 1.0


def test_string_true_false_infer_boolean():
    rows = _by_path(flatten_properties("o", {"a": "true", "b": "FALSE"}))
    assert rows["properties.a"].type == "boolean"
    assert rows["properties.b"].type == "boolean"
    # value_text stays verbatim (not normalised).
    assert rows["properties.a"].value_text == "true"
    assert rows["properties.b"].value_text == "FALSE"


# ───────────────────── numeric-string inference + UUID ──────────────────────


def test_numeric_string_inference():
    rows = _by_path(flatten_properties("o", {"a": "3.14", "b": " 42 ", "c": "1e3"}))
    assert rows["properties.a"].type == "number"
    assert rows["properties.a"].value_num == 3.14
    assert rows["properties.a"].value_text == "3.14"  # verbatim

    assert rows["properties.b"].type == "number"
    assert rows["properties.b"].value_num == 42.0

    assert rows["properties.c"].type == "number"
    assert rows["properties.c"].value_num == 1000.0


def test_uuid_like_string_rejected_from_number():
    rows = _by_path(flatten_properties("o", {"guid": "1-2-3", "g2": "a-b-c-d"}))
    assert rows["properties.guid"].type == "string"
    assert rows["properties.guid"].value_num is None
    assert rows["properties.g2"].type == "string"


def test_empty_and_whitespace_string_is_string():
    rows = _by_path(flatten_properties("o", {"a": "", "b": "   "}))
    assert rows["properties.a"].type == "string"
    assert rows["properties.b"].type == "string"


def test_non_finite_string_rejected():
    # "inf"/"nan" parse but fail the IsFinite guard → string.
    rows = _by_path(flatten_properties("o", {"a": "inf", "b": "nan"}))
    assert rows["properties.a"].type == "string"
    assert rows["properties.b"].type == "string"


def test_underscore_grouping_rejected():
    # Python float("1_000") == 1000 but C# NumberStyles.Float rejects it.
    rows = _by_path(flatten_properties("o", {"a": "1_000"}))
    assert rows["properties.a"].type == "string"


# ───────────────────────────── exclusions ──────────────────────────────────


def test_excluded_top_level_skipped_entirely():
    props = {
        "Autodesk Material": {"deep": {"x": 1}},
        "Document": {"y": 2},
        "Keep": {"z": 3},
    }
    rows = flatten_properties("o", props, excluded_top_level=DEFAULT_EXCLUDED_TOP_LEVEL)
    paths = {r.path for r in rows}

    assert not any(p.startswith("properties.Autodesk Material") for p in paths)
    assert not any(p.startswith("properties.Document") for p in paths)
    assert "properties.Keep.z" in paths


def test_exclusions_apply_at_top_level_only():
    # A nested "Document" key (not top-level) must NOT be excluded.
    props = {"Group": {"Document": {"x": 1}}}
    rows = flatten_properties("o", props, excluded_top_level=DEFAULT_EXCLUDED_TOP_LEVEL)
    assert "properties.Group.Document.x" in {r.path for r in rows}


def test_no_exclusions_by_default():
    props = {"Autodesk Material": {"x": 1}}
    rows = flatten_properties("o", props)
    assert "properties.Autodesk Material.x" in {r.path for r in rows}


# ───────────────────────────── MAX_DEPTH ───────────────────────────────────


def test_max_depth_cutoff():
    # Build properties.l0.l1...; depth counter starts at 0 for the contents of
    # `properties`, so a leaf is emitted only while depth < MAX_DEPTH.
    leaf: dict = {"leaf": 1}
    node: dict = leaf
    for _ in range(MAX_DEPTH + 3):
        node = {"n": node}
    rows = flatten_properties("o", node)
    # No row should have a path deeper than MAX_DEPTH segments under properties.
    for r in rows:
        segments = r.path.split(".")
        # "properties" + at most MAX_DEPTH levels
        assert len(segments) <= MAX_DEPTH + 1


def test_max_depth_emits_shallow_leaf():
    rows = flatten_properties("o", {"a": {"b": 1}})
    assert "properties.a.b" in {r.path for r in rows}


# ───────────────────────────── root scalars ────────────────────────────────


def test_root_scalars_emitted_from_mapping():
    scalars = {
        "name": "Wall",
        "applicationId": "guid-1",
        "speckle_type": "Objects.Data.DataObject",
    }
    rows = flatten_properties("o", {}, root_scalars=scalars)
    paths = _by_path(rows)
    assert paths["name"].value_text == "Wall"
    assert paths["name"].object_id == "o"
    assert "applicationId" in paths
    assert "speckle_type" in paths


def test_root_scalars_from_iterable_of_pairs():
    rows = flatten_properties("o", {}, root_scalars=[("name", "X"), ("level", 2)])
    paths = _by_path(rows)
    assert paths["name"].value_text == "X"
    assert paths["level"].type == "number"


def test_root_scalars_skip_non_scalar():
    rows = flatten_properties(
        "o", {}, root_scalars={"name": "X", "obj": {"a": 1}, "arr": [1, 2]}
    )
    paths = {r.path for r in rows}
    assert "name" in paths
    assert "obj" not in paths
    assert "arr" not in paths


# ───────────────────────────── parameter pattern ───────────────────────────


def test_parameter_pattern_name_value_units():
    props = {
        "Dimensions": {
            "Width": {
                "name": "Width",
                "value": 200.0,
                "units": "mm",
                "internalDefinitionName": "WIDTH",
            },
        }
    }
    rows = _by_path(flatten_properties("o", props))
    row = rows["properties.Dimensions.Width"]
    assert row.type == "number"
    assert row.value_num == 200.0
    assert row.units == "mm"
    assert row.internal_definition_name == "WIDTH"


def test_parameter_with_object_value_skipped():
    props = {"P": {"name": "P", "value": {"nested": 1}}}
    rows = flatten_properties("o", props)
    assert rows == []


# ───────────────────────────── lists skipped ───────────────────────────────


def test_lists_are_skipped():
    props = {"arr": [1, 2, 3], "keep": 5}
    rows = _by_path(flatten_properties("o", props))
    assert "properties.arr" not in rows
    assert "properties.keep" in rows


def test_none_values_skipped():
    rows = flatten_properties("o", {"a": None, "b": 1})
    assert {r.path for r in rows} == {"properties.b"}


# ───────────────────────────── material quantities ─────────────────────────


def test_material_quantities_extraction():
    props = {
        "Material Quantities": {
            "Concrete": {
                "materialCategory": "Structural",
                "area": {"value": 12.5, "units": "m2"},
                "volume": {"value": 3.0, "units": "m3"},
            }
        }
    }
    rows = _by_path(flatten_properties("o", props))
    area = rows["properties.Material Quantities.Structural.Concrete.area"]
    vol = rows["properties.Material Quantities.Structural.Concrete.volume"]
    assert area.value_num == 12.5
    assert area.units == "m2"
    assert vol.value_num == 3.0
    # The walk itself must NOT emit raw Material Quantities rows.
    assert not any(p.endswith(".materialCategory") for p in rows)


# ───────────────────────────── flatten_subtree ─────────────────────────────


def test_flatten_subtree_empty_object_id_and_prefix():
    rows = flatten_subtree({"Width": {"name": "Width", "value": 5}}, "type.Parameters")
    assert len(rows) == 1
    assert rows[0].path == "type.Parameters.Width"
    assert rows[0].object_id == ""


# ───────────────────────────── dispatcher ──────────────────────────────────


def test_flatten_object_properties_data_object():
    obj = {
        "speckle_type": "Objects.Data.DataObject",
        "name": "Wall",
        "applicationId": "guid",
        "properties": {"Pset": {"A": 1}},
    }
    rows = _by_path(flatten_object_properties("o", obj))
    assert rows["name"].value_text == "Wall"
    assert rows["applicationId"].value_text == "guid"
    assert rows["properties.Pset.A"].value_num == 1.0


def test_flatten_object_properties_missing_type_is_data_object():
    rows = flatten_object_properties("o", {"name": "X", "properties": {"a": 1}})
    assert "properties.a" in {r.path for r in rows}


def test_flatten_object_properties_instance_proxy_transform():
    transform = [
        1,
        0,
        0,
        10,
        0,
        1,
        0,
        20,
        0,
        0,
        1,
        30,
        0,
        0,
        0,
        1,
    ]
    obj = {
        "speckle_type": "Speckle.Core.Models.Instances.InstanceProxy",
        "units": "mm",
        "transform": transform,
    }
    rows = _by_path(flatten_object_properties("o", obj))
    assert rows["proxy.transform.tx"].value_num == 10.0
    assert rows["proxy.transform.ty"].value_num == 20.0
    assert rows["proxy.transform.tz"].value_num == 30.0
    assert rows["proxy.transform.tx"].units == "mm"
    assert "proxy.transform.matrix" in rows


def test_flatten_object_properties_collection_elements():
    obj = {
        "speckle_type": "Speckle.Core.Models.Collection",
        "name": "Layer",
        "elements": [{"referencedId": "id1"}, {"id": "id2"}, {"speckle_type": "x"}],
    }
    rows = _by_path(flatten_object_properties("o", obj))
    assert rows["name"].value_text == "Layer"
    assert rows["elements"].value_text == '["id1","id2"]'


def test_flatten_object_properties_geometry_returns_nothing():
    assert (
        flatten_object_properties("o", {"speckle_type": "Objects.Geometry.Mesh"}) == []
    )


def test_display_value_refs():
    obj = {
        "speckle_type": "Objects.Data.DataObject",
        "displayValue": [
            {"referencedId": "ref0"},
            {"id": "inl1"},
            {"speckle_type": "x"},
        ],
    }
    rows = _by_path(flatten_object_properties("o", obj))
    assert rows["displayValue.0.referencedId"].value_text == "ref0"
    assert rows["displayValue.1.referencedId"].value_text == "inl1"
    assert "displayValue.2.referencedId" not in rows


def test_location_extraction():
    obj = {
        "speckle_type": "Objects.Data.DataObject",
        "location": {"x": 1.0, "y": 2.0, "z": 3.0, "units": "m"},
    }
    rows = _by_path(flatten_object_properties("o", obj))
    assert rows["location.x"].value_num == 1.0
    assert rows["location.z"].units == "m"


def test_produces_rows():
    assert produces_rows("")
    assert produces_rows("Objects.Data.DataObject")
    assert produces_rows("Some.InstanceProxy")
    assert produces_rows("My.Collection")
    assert produces_rows("Some.Layer")
    assert not produces_rows("Objects.Geometry.Mesh")


# ───────────────────────────── constants ───────────────────────────────────


def test_constants_match_contract():
    assert frozenset({"Autodesk Material", "Document"}) == DEFAULT_EXCLUDED_TOP_LEVEL
    assert "Phase Created" in REVIT_EXCLUDED_TOP_LEVEL
    assert ROOT_SCALAR_FIELDS[0] == "name"
    assert "ifcType" in ROOT_SCALAR_FIELDS
