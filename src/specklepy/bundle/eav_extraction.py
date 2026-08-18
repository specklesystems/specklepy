"""EAV (Entity-Attribute-Value) property extraction for the bundle producer.

Ported from the .NET SDK's
``Speckle.Sdk/Pipelines/Send/Artifacts/EavExtraction.cs`` (itself a port of the
server's ``packages/shared/src/filtering/eavExtraction.ts``). Behaviour-parity
with the TS/C# implementations is the goal — quirks are intentionally preserved.

Unlike the C# JObject path, the Python input is an already-parsed
``dict[str, Any]`` tree (the IFC converter builds ``DataObject.properties`` as
nested dicts), so this mirrors the C# *native* (``Dictionary``) flatten path:
``WalkPropertiesNative`` / ``FlattenProperties`` / ``FlattenSubtree``.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any, NamedTuple

MAX_DEPTH = 10
"""Recursion cutoff for the property walk (EavExtraction.cs:31)."""


class EavRow(NamedTuple):
    """One flat property row destined for the eav table (EavExtraction.cs:12-20)."""

    object_id: str
    path: str
    value_text: str
    value_num: float | None
    type: str  # "string" | "number" | "boolean"
    units: str | None
    internal_definition_name: str | None


# Universal top-level keys under `properties` excluded for every source
# (EavExtraction.cs:42-46).
DEFAULT_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset(
    {"Autodesk Material", "Document"}
)

# Revit-specific top-level categories to skip (EavExtraction.cs:59-73). Exposed
# for parity even though IFC won't use it.
REVIT_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "Line Style",
        "SketchPlane",
        "GeometryCurve",
        "Element ID",
        "Category",
        "CreatedPhaseId",
        "Id",
        "Material",
        "Revit Material",
        "Orientation",
        "ParametersMap",
        "Phase Created",
    }
)

# Root-level fields to index (outside of `properties`) (EavExtraction.cs:76-89).
ROOT_SCALAR_FIELDS: tuple[str, ...] = (
    "name",
    "type",
    "family",
    "category",
    "level",
    "units",
    "speckle_type",
    "applicationId",
    "definitionId",
    "ifcType",
    "path",
)

# Rejects UUID-like strings ("a-b-c" shapes) from numeric inference
# (EavExtraction.cs:92).
_UUID_LIKE = re.compile(r".-.-")


# ───────────────────────────── scalar helpers ──────────────────────────────


def _is_scalar(value: Any) -> bool:
    """Mirror IsScalar (EavExtraction.cs:775). In Python ``bool`` subclasses
    ``int``, so it is covered here and dispatched first everywhere below."""
    return isinstance(value, bool | int | float | str)


def _try_parse_float(text: str) -> float | None:
    """C# ``double.TryParse(.., NumberStyles.Float, InvariantCulture)`` analogue.

    ``NumberStyles.Float`` allows leading/trailing whitespace, sign, decimal
    point and exponent — which ``float()`` also accepts. It does NOT allow digit
    group separators, so reject Python's ``_`` grouping. ``inf``/``nan`` strings
    are accepted by both but later rejected by the IsFinite guard at the caller.
    """
    if "_" in text:
        return None
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _infer_type(value: Any) -> str:
    """Port of InferTypeNative (EavExtraction.cs:797-828)."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, float):
        return "number" if math.isfinite(value) else "string"
    if isinstance(value, int):
        return "number"
    if isinstance(value, str):
        if value.lower() in ("true", "false"):
            return "boolean"
        trimmed = value.strip()
        if not trimmed or _UUID_LIKE.search(trimmed):
            return "string"
        num = _try_parse_float(trimmed)
        return "number" if num is not None and math.isfinite(num) else "string"
    return "string"


def _to_num(value: Any) -> float | None:
    """Port of ToNumNative (EavExtraction.cs:830-846). Only called when the
    inferred type is ``"number"``."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        d = float(value)
        return d if math.isfinite(d) else None
    if isinstance(value, str):
        num = _try_parse_float(value.strip())
        return num if num is not None and math.isfinite(num) else None
    return None


def _float_to_text(d: float) -> str:
    """JS ``String(number)`` / C# ``"R"`` semantics: integral floats drop the
    trailing ``.0`` (EavExtraction.cs:790)."""
    if math.isnan(d):
        return "NaN"
    if math.isinf(d):
        return "Infinity" if d > 0 else "-Infinity"
    if d.is_integer() and abs(d) < 1e16:
        return str(int(d))
    return repr(d)


def _to_text(value: Any) -> str:
    """Port of ToTextNative (EavExtraction.cs:785-795): lowercase booleans,
    strings verbatim, invariant numbers."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return _float_to_text(value)
    if isinstance(value, int):
        return str(value)
    return str(value)


def _make_row(
    object_id: str,
    path: str,
    value: Any,
    units: str | None,
    internal_definition_name: str | None,
) -> EavRow:
    """Port of MakeRowNative (EavExtraction.cs:778-783)."""
    inferred = _infer_type(value)
    value_num = _to_num(value) if inferred == "number" else None
    return EavRow(
        object_id,
        path,
        _to_text(value),
        value_num,
        inferred,
        units,
        internal_definition_name,
    )


def _finite_number(token: Any) -> float | None:
    """Port of TryGetFiniteNumber (EavExtraction.cs:555-568): int/float only
    (booleans excluded), finite."""
    if isinstance(token, bool):
        return None
    if isinstance(token, int | float):
        d = float(token)
        return d if math.isfinite(d) else None
    return None


# ───────────────────────────── core walk ───────────────────────────────────


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _ref_id(entry: Mapping[str, Any]) -> str | None:
    """``referencedId`` (if a string) else ``id`` (if a string), matching the C#
    ``Type == String`` checks — an empty-string ``referencedId`` still wins."""
    rid = entry.get("referencedId")
    if isinstance(rid, str):
        return rid
    eid = entry.get("id")
    return eid if isinstance(eid, str) else None


def _walk_properties(
    object_id: str,
    obj: Mapping[str, Any],
    prefix: str,
    depth: int,
    rows: list[EavRow],
    excluded: frozenset[str] | set[str] | None,
) -> None:
    """Port of WalkPropertiesNative (EavExtraction.cs:666-732). Exclusions apply
    at depth 0 only; recursion drops them."""
    if depth >= MAX_DEPTH:
        return

    for key, val in obj.items():
        if depth == 0 and excluded and key in excluded:
            continue
        if val is None:
            continue

        path = f"{prefix}.{key}"

        if isinstance(val, dict):
            # Parameter pattern { name, value } → single row at this path.
            if "name" in val and "value" in val:
                param_val = val.get("value")
                if not _is_scalar(param_val):
                    continue
                rows.append(
                    _make_row(
                        object_id,
                        path,
                        param_val,
                        _str_or_none(val.get("units")),
                        _str_or_none(val.get("internalDefinitionName")),
                    )
                )
                continue

            # Parity with the JObject walk's special-cases.
            if key == "Structure" and prefix.endswith(".Type Parameters"):
                continue
            if key == "Material Quantities":
                continue  # handled separately

            _walk_properties(object_id, val, path, depth + 1, rows, None)
            continue

        if _is_scalar(val):
            rows.append(_make_row(object_id, path, val, None, None))
        # non-scalar, non-dict (lists/arrays, etc.) → skipped, as in C#.


def _extract_material_quantities(
    object_id: str, mat_quants: Mapping[str, Any], rows: list[EavRow]
) -> None:
    """Port of ExtractMaterialQuantitiesNative (EavExtraction.cs:734-750)."""
    for mat_name, mat in mat_quants.items():
        if not isinstance(mat, dict):
            continue
        category = _str_or_none(mat.get("materialCategory")) or "Unknown"
        _append_quantity(object_id, mat, "area", category, mat_name, rows)
        _append_quantity(object_id, mat, "volume", category, mat_name, rows)


def _append_quantity(
    object_id: str,
    mat: Mapping[str, Any],
    kind: str,
    category: str,
    mat_name: str,
    rows: list[EavRow],
) -> None:
    """Port of AppendQuantityNative (EavExtraction.cs:752-773)."""
    q = mat.get(kind)
    if not isinstance(q, dict):
        return
    value = q.get("value")
    if not _is_scalar(value):
        return
    rows.append(
        _make_row(
            object_id,
            f"properties.Material Quantities.{category}.{mat_name}.{kind}",
            value,
            _str_or_none(q.get("units")),
            None,
        )
    )


# ───────────────────────────── public API ──────────────────────────────────


def flatten_properties(
    application_id: str,
    properties: Mapping[str, Any],
    root_scalars: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
    excluded_top_level: frozenset[str] | set[str] | None = None,
) -> list[EavRow]:
    """Flatten an object's native property tree to EAV rows.

    Port of FlattenProperties (EavExtraction.cs:585-613). ``root_scalars`` are
    bare top-level fields emitted under their plain key; ``properties`` is walked
    under the ``properties.`` prefix; Revit ``Material Quantities`` is extracted
    with its special structure.

    Args:
        application_id: the object id every emitted row is keyed by.
        properties: the nested ``properties`` dict to walk.
        root_scalars: optional mapping or iterable of ``(key, value)`` pairs;
            only scalar values are emitted (one row each).
        excluded_top_level: top-level keys under ``properties`` to skip wholesale
            (the entire subtree is dropped). ``None`` extracts everything.
    """
    rows: list[EavRow] = []

    if root_scalars is not None:
        items = (
            root_scalars.items() if isinstance(root_scalars, Mapping) else root_scalars
        )
        for key, value in items:
            if _is_scalar(value):
                rows.append(_make_row(application_id, key, value, None, None))

    _walk_properties(
        application_id, properties, "properties", 0, rows, excluded_top_level
    )

    mq = properties.get("Material Quantities")
    if isinstance(mq, dict):
        _extract_material_quantities(application_id, mq, rows)

    return rows


def flatten_subtree(subtree: Mapping[str, Any], path_prefix: str) -> list[EavRow]:
    """Flatten a property SUBTREE under ``path_prefix`` — used to route Type/
    System parameter trees into ``type_eav``. Rows carry an empty object id (the
    caller keys them by ``type_index``). Port of FlattenSubtree
    (EavExtraction.cs:621-625)."""
    rows: list[EavRow] = []
    _walk_properties("", subtree, path_prefix, 0, rows, None)
    return rows


def flatten_object_properties(
    object_id: str,
    obj: Mapping[str, Any],
    excluded: frozenset[str] | set[str] | None = None,
) -> list[EavRow]:
    """Dispatch on ``speckle_type`` and extract EAV rows for a whole parsed
    object. Port of FlattenObjectProperties (EavExtraction.cs:110-131):
    InstanceProxy → root scalars + transform; DataObject (or missing type) →
    full extraction; Collection/Layer → root scalars + properties + elements;
    everything else → no rows."""
    speckle_type = _str_or_none(obj.get("speckle_type")) or ""

    if "InstanceProxy" in speckle_type:
        return _extract_instance_proxy(object_id, obj)
    if speckle_type == "" or speckle_type.startswith("Objects.Data."):
        return _extract_data_object(object_id, obj, excluded)
    if _is_collection_type(speckle_type):
        return _extract_collection(object_id, obj, excluded)
    return []


def produces_rows(speckle_type: str) -> bool:
    """Cheap pre-check matching the dispatch in :func:`flatten_object_properties`
    (EavExtraction.cs:138-142)."""
    return (
        speckle_type == ""
        or "InstanceProxy" in speckle_type
        or speckle_type.startswith("Objects.Data.")
        or _is_collection_type(speckle_type)
    )


def _is_collection_type(speckle_type: str) -> bool:
    """Port of IsCollectionType (EavExtraction.cs:144-151)."""
    return speckle_type.endswith(".Layer") or "Collection" in speckle_type


def _extract_root_scalars(
    object_id: str, obj: Mapping[str, Any], rows: list[EavRow]
) -> None:
    """Port of ExtractRootScalars (EavExtraction.cs:253-268)."""
    for field in ROOT_SCALAR_FIELDS:
        val = obj.get(field)
        if val is None:
            continue
        if isinstance(val, dict | list):
            continue
        if _is_scalar(val):
            rows.append(_make_row(object_id, field, val, None, None))


def _extract_data_object(
    object_id: str,
    obj: Mapping[str, Any],
    excluded: frozenset[str] | set[str] | None,
) -> list[EavRow]:
    """Port of ExtractDataObject (EavExtraction.cs:153-196)."""
    rows: list[EavRow] = []
    _extract_root_scalars(object_id, obj, rows)

    props = obj.get("properties")
    if isinstance(props, dict):
        _walk_properties(object_id, props, "properties", 0, rows, excluded)
        mq = props.get("Material Quantities")
        if isinstance(mq, dict):
            _extract_material_quantities(object_id, mq, rows)

    loc = obj.get("location")
    if isinstance(loc, dict):
        _extract_location(object_id, loc, rows)

    dv = obj.get("displayValue")
    if isinstance(dv, list):
        _extract_display_value_refs(object_id, dv, rows)

    elements = obj.get("elements")
    if isinstance(elements, list):
        _extract_elements_refs(object_id, elements, rows)

    return rows


def _extract_instance_proxy(object_id: str, obj: Mapping[str, Any]) -> list[EavRow]:
    """Port of ExtractInstanceProxy (EavExtraction.cs:198-227)."""
    rows: list[EavRow] = []
    _extract_root_scalars(object_id, obj, rows)

    units = _str_or_none(obj.get("units"))
    transform = obj.get("transform")
    if isinstance(transform, list) and len(transform) == 16:
        for idx, suffix in ((3, "tx"), (7, "ty"), (11, "tz")):
            v = _finite_number(transform[idx])
            if v is not None:
                rows.append(
                    _make_row(object_id, f"proxy.transform.{suffix}", v, units, None)
                )
        rows.append(
            _make_row(
                object_id,
                "proxy.transform.matrix",
                json.dumps(transform, separators=(",", ":")),
                units,
                None,
            )
        )

    return rows


def _extract_collection(
    object_id: str,
    obj: Mapping[str, Any],
    excluded: frozenset[str] | set[str] | None,
) -> list[EavRow]:
    """Port of ExtractCollection (EavExtraction.cs:229-251)."""
    rows: list[EavRow] = []
    _extract_root_scalars(object_id, obj, rows)

    props = obj.get("properties")
    if isinstance(props, dict):
        _walk_properties(object_id, props, "properties", 0, rows, excluded)

    elements = obj.get("elements")
    if isinstance(elements, list):
        _extract_elements_refs(object_id, elements, rows)

    return rows


def _extract_location(
    object_id: str, loc: Mapping[str, Any], rows: list[EavRow]
) -> None:
    """Port of ExtractLocation (EavExtraction.cs:270-280)."""
    units = _str_or_none(loc.get("units"))
    for axis in ("x", "y", "z"):
        v = _finite_number(loc.get(axis))
        if v is not None:
            rows.append(_make_row(object_id, f"location.{axis}", v, units, None))


def _extract_display_value_refs(
    object_id: str, dv: list[Any], rows: list[EavRow]
) -> None:
    """Port of ExtractDisplayValueRefs (EavExtraction.cs:282-306)."""
    for i, entry in enumerate(dv):
        if not isinstance(entry, dict):
            continue
        ref_id = _ref_id(entry)
        if ref_id is not None:
            rows.append(
                _make_row(
                    object_id, f"displayValue.{i}.referencedId", ref_id, None, None
                )
            )


def _extract_elements_refs(
    object_id: str, elements: list[Any], rows: list[EavRow]
) -> None:
    """Port of ExtractElementsRefs (EavExtraction.cs:308-332). All child refs are
    serialised into a single JSON array stored in ``value_text``."""
    ref_ids: list[str] = []
    for entry in elements:
        if not isinstance(entry, dict):
            continue
        ref_id = _ref_id(entry)
        if ref_id is not None:
            ref_ids.append(ref_id)
    if not ref_ids:
        return
    rows.append(
        _make_row(
            object_id,
            "elements",
            json.dumps(ref_ids, separators=(",", ":")),
            None,
            None,
        )
    )
