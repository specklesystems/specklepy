"""Model-scoped placement + CRS rows (``eav.model``) from IFC georeferencing.

Mirrors the C# Revit producer's modelPlacement contract (ENG-9099): transforms map
the stored internal frame → the named datum's space, emitted whether or not anything
was baked into geometry. speckleifc never rebases coordinates, so ``default`` is
``internalOrigin`` (identity) and ``appliedToGeometry`` is false; the IFC map
conversion, when present, rides as the ``mapConversion`` option.
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
from ifcopenshell import file
from ifcopenshell.util import geolocation
from ifcopenshell.util.unit import calculate_unit_scale

from specklepy.bundle.builder import BundleBuilder

logger = logging.getLogger(__name__)

IDENTITY = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)  # fmt: skip

_CRS_UNIT_NAMES = {
    "METRE": "m",
    "MILLIMETRE": "mm",
    "CENTIMETRE": "cm",
    "FOOT": "ft",
    "INCH": "in",
}


def emit_georeferencing(ifc_file: file, builder: BundleBuilder) -> None:
    options: dict[str, tuple[float, ...]] = {"internalOrigin": IDENTITY}
    map_transform = _map_conversion_transform(ifc_file)
    if map_transform is not None:
        options["mapConversion"] = map_transform
    builder.add_model_placement("internalOrigin", IDENTITY, "m", False, options=options)
    _emit_crs(ifc_file, builder)
    _emit_true_north(ifc_file, builder)
    _emit_site_anchor(ifc_file, builder)
    _warn_on_non_identity_wcs(ifc_file)


def _map_conversion_transform(ifc_file: file) -> tuple[float, ...] | None:
    try:
        if geolocation.get_helmert_transformation_parameters(ifc_file) is None:
            return None
        # local (project units) → map units; stored coordinates are metres, so
        # pre-scale metres → project units.
        local_to_map = geolocation.auto_local2global(
            ifc_file, np.eye(4), should_return_in_map_units=True
        )
        unit_scale = calculate_unit_scale(ifc_file)  # project length unit → metres
        metres_to_local = np.diag([1.0 / unit_scale] * 3 + [1.0])
        return tuple(float(v) for v in (local_to_map @ metres_to_local).flatten())
    except Exception:
        logger.warning("Failed to derive the IFC map conversion", exc_info=True)
        return None


def _emit_crs(ifc_file: file, builder: BundleBuilder) -> None:
    try:
        crs: dict[str, Any] | None = geolocation.get_crs(ifc_file)
    except Exception:
        logger.warning("Failed to read the projected CRS", exc_info=True)
        return
    if not crs:
        return
    name = crs.get("Name")
    if name:
        builder.add_model_property("crs.horizontal.nativeCode", str(name))
        authority, _, code = str(name).partition(":")
        if code:
            builder.add_model_property("crs.horizontal.authority", authority)
            builder.add_model_property("crs.horizontal.code", code)
    description = crs.get("Description")
    if description:
        builder.add_model_property("crs.horizontal.definition", str(description))
    units = _crs_units(crs.get("MapUnit"))
    if units:
        builder.add_model_property("crs.units", units)


def _crs_units(map_unit: Any) -> str | None:
    if map_unit is None:
        return None
    try:
        from ifcopenshell.util.unit import get_full_unit_name

        return _CRS_UNIT_NAMES.get(get_full_unit_name(map_unit).upper())
    except Exception:
        return None


def _emit_true_north(ifc_file: file, builder: BundleBuilder) -> None:
    # get_true_north returns 0 both for "absent" and a genuine 0° — only emit when a
    # TrueNorth direction is authored.
    try:
        contexts = ifc_file.by_type(
            "IfcGeometricRepresentationContext", include_subtypes=False
        )
        if not any(getattr(c, "TrueNorth", None) for c in contexts):
            return
        degrees = geolocation.get_true_north(ifc_file)
    except Exception:
        logger.warning("Failed to read TrueNorth", exc_info=True)
        return
    builder.add_model_property(
        "projectLocation.trueNorthAngle", math.radians(degrees), "rad"
    )


def _emit_site_anchor(ifc_file: file, builder: BundleBuilder) -> None:
    try:
        sites = ifc_file.by_type("IfcSite")
    except Exception:
        return
    if not sites:
        return
    site = sites[0]
    latitude = _dms_to_decimal(getattr(site, "RefLatitude", None))
    longitude = _dms_to_decimal(getattr(site, "RefLongitude", None))
    if latitude is None or longitude is None:
        return
    builder.add_model_property("geolocation.anchor.latitude", latitude, "deg")
    builder.add_model_property("geolocation.anchor.longitude", longitude, "deg")
    elevation = getattr(site, "RefElevation", None)
    if elevation is not None:
        try:
            builder.add_model_property(
                "geolocation.anchor.elevation",
                float(elevation) * calculate_unit_scale(ifc_file),
                "m",
            )
        except Exception:
            logger.warning("Failed to convert RefElevation", exc_info=True)
    builder.add_model_property("geolocation.anchor.source", "ifcSite")


def _dms_to_decimal(dms: Any) -> float | None:
    if not dms:
        return None
    try:
        return geolocation.dms2dd(*list(dms)[:4])
    except Exception:
        logger.warning("Failed to convert site lat/long %s", dms, exc_info=True)
        return None


def _warn_on_non_identity_wcs(ifc_file: file) -> None:
    try:
        wcs = geolocation.get_wcs(ifc_file)
    except Exception:
        return
    if wcs is not None and not np.allclose(wcs, np.eye(4)):
        # the geometry iterator does not apply the context WCS; stored coordinates
        # are neither local nor WCS-based for such files
        logger.warning(
            "IFC WorldCoordinateSystem is not identity; stored coordinates do not "
            "include it"
        )
