"""ENG-9524: Body representations filed under a *Plan* context, plus one curve in a
Model sub-context. IfcOpenShell's default context selection keeps only the Model family
and, because the sub-context is not empty, never falls back to "all contexts" — the file
reads as having no geometry. The importer must retry with the contexts the 3D
representations actually reference (ICPrefab / iTConcrete precast exports)."""

from __future__ import annotations

import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")  # requires the [speckleifc] extra

from speckleifc.ifc_geometry_processing import (  # noqa: E402
    contexts_for_3d_representations,
    create_geometry_iterator,
)
from speckleifc.importer import ImportJob  # noqa: E402


class _NoProgress:
    def report(self, progress_message: str, progress: float | None) -> None:
        pass

    def should_report_progress(self) -> bool:
        return False


def _axis(f, origin=(0.0, 0.0, 0.0)):
    return f.create_entity(
        "IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=origin),
    )


def _plan_context_body_file(with_grid: bool):
    f = ifcopenshell.file(schema="IFC2X3")
    project = f.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Precast"
    )
    project.UnitsInContext = f.create_entity(
        "IfcUnitAssignment",
        Units=[
            f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
            f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN"),
        ],
    )
    wcs = _axis(f)
    plan = f.create_entity(
        "IfcGeometricRepresentationContext",
        ContextType="Plan",
        CoordinateSpaceDimension=3,
        Precision=1e-6,
        WorldCoordinateSystem=wcs,
    )
    model = f.create_entity(
        "IfcGeometricRepresentationContext",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-6,
        WorldCoordinateSystem=wcs,
    )
    footprint = f.create_entity(
        "IfcGeometricRepresentationSubContext",
        ContextIdentifier="FootPrint",
        ContextType="Model",
        ParentContext=model,
        TargetView="MODEL_VIEW",
    )
    project.RepresentationContexts = [plan, model]

    storey = f.create_entity(
        "IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), Name="Floor 16"
    )
    f.create_entity(
        "IfcRelAggregates",
        GlobalId=ifcopenshell.guid.new(),
        RelatingObject=project,
        RelatedObjects=[storey],
    )

    # The exporter's quirk: a perfectly good extruded solid, Body identifier, but
    # attached to the Plan context.
    profile = f.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        Position=f.create_entity(
            "IfcAxis2Placement2D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
        ),
        XDim=1.0,
        YDim=0.5,
    )
    solid = f.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=_axis(f),
        ExtrudedDirection=f.create_entity(
            "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
        ),
        Depth=0.3,
    )
    body = f.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=plan,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    beam = f.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=ifcopenshell.guid.new(),
        Name="Prefab beam",
        ObjectPlacement=f.create_entity(
            "IfcLocalPlacement", RelativePlacement=_axis(f)
        ),
        Representation=f.create_entity(
            "IfcProductDefinitionShape", Representations=[body]
        ),
    )
    elements = [beam]

    if with_grid:
        # One curve in the Model sub-context is enough to defeat IfcOpenShell's
        # "no representations in relevant contexts, using all" fallback.
        line = f.create_entity(
            "IfcPolyline",
            Points=[
                f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
                f.create_entity("IfcCartesianPoint", Coordinates=(10.0, 0.0, 0.0)),
            ],
        )
        grid_axis = f.create_entity(
            "IfcGridAxis", AxisTag="A", AxisCurve=line, SameSense=True
        )
        grid_rep = f.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=footprint,
            RepresentationIdentifier="FootPrint",
            RepresentationType="GeometricCurveSet",
            Items=[f.create_entity("IfcGeometricCurveSet", Elements=[line])],
        )
        grid = f.create_entity(
            "IfcGrid",
            GlobalId=ifcopenshell.guid.new(),
            Name="Grid",
            ObjectPlacement=f.create_entity(
                "IfcLocalPlacement", RelativePlacement=_axis(f)
            ),
            Representation=f.create_entity(
                "IfcProductDefinitionShape", Representations=[grid_rep]
            ),
            UAxes=[grid_axis],
            VAxes=[],
        )
        elements.append(grid)

    f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatingStructure=storey,
        RelatedElements=elements,
    )
    return f, plan, model, footprint


def test_context_ids_are_a_superset_of_the_default_widened_by_body_contexts():
    f, plan, model, footprint = _plan_context_body_file(with_grid=True)
    assert contexts_for_3d_representations(f) == sorted(
        {plan.id(), model.id(), footprint.id()}
    )


def test_default_selection_misses_plan_context_bodies_when_a_model_curve_exists():
    """Pins the IfcOpenShell behaviour the retry exists for. If this starts passing
    with the default iterator, the fallback has become unnecessary upstream."""
    f, *_ = _plan_context_body_file(with_grid=True)
    assert create_geometry_iterator(f).initialize() is False
    assert create_geometry_iterator(f, contexts_for_3d_representations(f)).initialize()


def test_default_selection_still_finds_plan_context_bodies_without_the_curve():
    f, *_ = _plan_context_body_file(with_grid=False)
    assert create_geometry_iterator(f).initialize()


def test_import_job_converts_the_beam_via_the_context_retry(tmp_path):
    f, *_ = _plan_context_body_file(with_grid=True)
    job = ImportJob(f, str(tmp_path), "precast", _NoProgress())
    job.run()
    assert job.geometries_count == 1
