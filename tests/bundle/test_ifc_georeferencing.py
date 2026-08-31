"""emit_georeferencing over synthetic IFC4 files: the map conversion becomes the
``mapConversion`` placement option (internal metres → map units), the projected CRS,
true north and site anchor land as model rows, and none of them appear when the file
carries no georeferencing."""

from __future__ import annotations

import math

import duckdb
import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

from speckleifc.converter.model import emit_georeferencing  # noqa: E402
from specklepy.bundle import BundleBuilder, Producer  # noqa: E402

BASE = "geo"


def _project_with_units(f):
    proj = f.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Project"
    )
    si = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    proj.UnitsInContext = f.create_entity("IfcUnitAssignment", Units=[si])
    return proj, si


def _georeferenced_file():
    f = ifcopenshell.file(schema="IFC4")
    proj, si = _project_with_units(f)
    ctx = f.create_entity(
        "IfcGeometricRepresentationContext",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        WorldCoordinateSystem=f.create_entity(
            "IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        ),
        TrueNorth=f.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0)),
    )
    proj.RepresentationContexts = [ctx]
    crs = f.create_entity(
        "IfcProjectedCRS",
        Name="EPSG:25832",
        Description="ETRS89 / UTM 32N",
        MapUnit=si,
    )
    f.create_entity(
        "IfcMapConversion",
        SourceCRS=ctx,
        TargetCRS=crs,
        Eastings=1000.0,
        Northings=2000.0,
        OrthogonalHeight=50.0,
        XAxisAbscissa=1.0,
        XAxisOrdinate=0.0,
        Scale=1.0,
    )
    f.create_entity(
        "IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        RefLatitude=(51, 30, 0, 0),
        RefLongitude=(0, 7, 39, 0),
        RefElevation=12.5,
    )
    return f


def _model_rows(out: str) -> dict:
    return {
        path: (s, d, b, unit)
        for path, s, d, b, unit in duckdb.sql(
            f"SELECT path, value_string, value_double, value_boolean, unit "
            f"FROM read_parquet('{out}/{BASE}.eav.model.parquet')"
        ).fetchall()
    }


def _emit(f, tmp_path) -> dict:
    out = str(tmp_path)
    builder = BundleBuilder(Producer("ifc", "0.8.5"), "m", out, BASE)
    emit_georeferencing(f, builder)
    builder.pipeline.intern_object("x")  # a bundle needs at least the objects table
    builder.build()
    return _model_rows(out)


def test_georeferenced_file_emits_full_row_set(tmp_path):
    rows = _emit(_georeferenced_file(), tmp_path)

    assert rows["modelPlacement.default"][0] == "internalOrigin"
    assert rows["modelPlacement.source"][0] == "internalOrigin"
    assert rows["modelPlacement.units"][0] == "m"
    assert rows["modelPlacement.appliedToGeometry"][2] is False

    # identity rotation + scale 1 in a metre file → pure E/N/H translation
    transform = [
        float(v)
        for v in rows["modelPlacement.options.mapConversion.transform"][0].split(",")
    ]
    assert transform[3] == 1000.0
    assert transform[7] == 2000.0
    assert transform[11] == 50.0
    assert transform[0] == transform[5] == transform[10] == transform[15] == 1.0

    assert rows["crs.horizontal.authority"][0] == "EPSG"
    assert rows["crs.horizontal.code"][0] == "25832"
    assert rows["crs.horizontal.nativeCode"][0] == "EPSG:25832"
    assert rows["crs.horizontal.definition"][0] == "ETRS89 / UTM 32N"
    assert rows["crs.units"][0] == "m"

    assert rows["projectLocation.trueNorthAngle"][1] == pytest.approx(0.0)
    assert rows["projectLocation.trueNorthAngle"][3] == "rad"

    assert rows["geolocation.anchor.latitude"][1] == pytest.approx(51.5)
    assert rows["geolocation.anchor.latitude"][3] == "deg"
    assert rows["geolocation.anchor.longitude"][1] == pytest.approx(0.1275, abs=1e-4)
    assert rows["geolocation.anchor.elevation"][1] == pytest.approx(12.5)
    assert rows["geolocation.anchor.source"][0] == "ifcSite"


def test_map_conversion_scales_from_project_units(tmp_path):
    f = _georeferenced_file()
    # switch the project length unit to millimetres: stored metres must be
    # rescaled into project units before the helmert step
    si = f.by_type("IfcSIUnit")[0]
    si.Prefix = "MILLI"
    rows = _emit(f, tmp_path)
    transform = [
        float(v)
        for v in rows["modelPlacement.options.mapConversion.transform"][0].split(",")
    ]
    assert transform[0] == pytest.approx(1000.0)  # 1 m = 1000 project units
    assert transform[3] == pytest.approx(1000.0)  # E/N/H stay map-unit absolute
    assert transform[7] == pytest.approx(2000.0)


def test_bare_file_emits_baseline_only(tmp_path):
    f = ifcopenshell.file(schema="IFC4")
    _project_with_units(f)
    rows = _emit(f, tmp_path)
    placement_paths = {p for p in rows if p.startswith("modelPlacement.")}
    assert placement_paths == {
        "modelPlacement.default",
        "modelPlacement.source",
        "modelPlacement.transform",
        "modelPlacement.units",
        "modelPlacement.appliedToGeometry",
        "modelPlacement.options.internalOrigin.transform",
    }
    assert not any(
        p.startswith(("crs.", "geolocation.", "projectLocation.")) for p in rows
    )


def test_true_north_angle_is_radians(tmp_path):
    f = _georeferenced_file()
    ctx = f.by_type("IfcGeometricRepresentationContext", include_subtypes=False)[0]
    # rotate true north 30° anticlockwise
    ctx.TrueNorth.DirectionRatios = (
        -math.sin(math.radians(30)),
        math.cos(math.radians(30)),
    )
    rows = _emit(f, tmp_path)
    assert rows["projectLocation.trueNorthAngle"][1] == pytest.approx(math.radians(30))
