"""Builds one bundle that exercises every writer; shared by the pipeline test and the
spec-validator conformance run."""

from __future__ import annotations

from dataclasses import dataclass

from specklepy.bundle import CameraView, ObjectsArtifactPipeline, Producer
from specklepy.bundle.envelope_writer import SceneView, SceneViewKey
from specklepy.bundle.spec import Rel
from specklepy.objects.annotation.text import Text
from specklepy.objects.geometry import Plane, Point, Polyline, Region, Vector
from specklepy.objects.geometry.mesh import Mesh

PRODUCER = Producer(slug="fixture", version="0.1", migrated_from_schema_version=None)
IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
PLACEMENT = [1, 0, 0, 30.5, 0, 1, 0, 12.2, 0, 0, 1, 0, 0, 0, 0, 1]


def mesh() -> Mesh:
    return Mesh(
        vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        faces=[3, 0, 1, 2],
        units="m",
    )


def plane() -> Plane:
    return Plane(
        origin=Point(x=0, y=0, z=0, units="m"),
        normal=Vector(x=0, y=0, z=1, units="m"),
        xdir=Vector(x=1, y=0, z=0, units="m"),
        ydir=Vector(x=0, y=1, z=0, units="m"),
        units="m",
    )


def region() -> Region:
    square = Polyline(value=[0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0], units="m")
    square.closed = True
    return Region(
        boundary=square,
        innerLoops=[],
        hasHatchPattern=False,
        displayValue=[],
        units="m",
    )


def text() -> Text:
    return Text(
        value="Hi",
        origin=Point(x=0, y=0, z=0, units="m"),
        height=2.5,
        plane=plane(),
        units="m",
    )


@dataclass(frozen=True)
class Ks:
    wall: int
    member: int
    placed: int
    nested_member: int
    inner_member: int
    host: int
    mesh_geo: int
    region_geo: int
    text_geo: int
    definition: int
    inner_definition: int
    instance: int
    nested_instance: int
    material: int
    color: int
    level: int
    layer: int
    model: int
    system: int
    system2: int
    group: int


def build(out: str, base: str) -> Ks:
    with ObjectsArtifactPipeline(out, base, PRODUCER) as p:
        wall = p.intern_object("wall-1")
        p.add_properties(
            "wall-1",
            {"Pset_Wall": {"Width": 200, "LoadBearing": True}},
            root_scalars=[("name", "Wall-1"), ("ifcType", "IfcWall")],
        )
        member = p.intern_object("member-1")
        placed = p.intern_object("placed-1")
        nested_member = p.intern_object("nested-member-1")
        inner_member = p.intern_object("inner-member-1")
        host = p.intern_object("host-1")

        mesh_geo = p.add_geometry("mesh-1", mesh())
        region_geo = p.add_geometry("region-1", region())
        text_geo = p.add_geometry("text-1", text())
        member_geo = p.add_geometry("mesh-member", mesh())
        inner_geo = p.add_geometry("mesh-inner", mesh())

        p.display(wall, mesh_geo, 0)
        p.display(wall, region_geo, 1)
        p.display(wall, text_geo, 2)

        material = p.add_material(
            "mat-1",
            -1,
            1.0,
            0.0,
            0.5,
            name="Painted Steel",
            emissive=0xFF00FF00,
            ior=1.45,
        )
        p.add_material("mat-black", -1, 1.0, 0.0, 0.5, emissive=0xFF000000)
        color = p.add_color(0xFFFF0000)
        p.has_material(mesh_geo, material)
        p.has_color(mesh_geo, color)
        p.object_has_material(wall, material)
        p.object_has_color(wall, color)

        inner_definition = p.add_definition("def-inner", "Bolt")
        p.defines(inner_definition, inner_geo, 0)
        p.defines_member(inner_definition, inner_member, 0)
        nested_instance = p.add_instance(
            "place-nested", inner_definition, IDENTITY, "m"
        )

        definition = p.add_definition("def-1", "WallBody")
        p.defines(definition, member_geo, 0)
        p.defines_member(definition, member, 0)
        p.defines_instance(definition, nested_instance, 1)
        p.defines_member(definition, nested_member, 1)
        p.places(nested_member, nested_instance)

        instance = p.add_instance("place-1", definition, IDENTITY, "m")
        p.display_instance(placed, instance, 0)

        layer = p.add_collection("layer-1", "Walls", None, "Layer", gh_topology="0-1")
        p.in_collection(wall, layer, 0)
        p.node_has_material(layer, material)
        p.node_has_color(layer, color)

        level = p.add_level("lvl-1", "L1", 3.0)
        p.on_level(wall, level)
        model = p.add_container("model-1", "Host", None, "Model")
        p.in_model(wall, model, 0)
        system = p.add_container("sys-1", "Hot Water", None, "MEP System")
        p.in_system(wall, system, 0)
        system2 = p.add_container("sys-2", "Return Air", None, "MEP System")
        p.in_system(wall, system2, 0)
        group = p.add_container("grp-1", "Group A", None, "Group")
        p.in_group(wall, group, 0)

        p.subelement(wall, host, 0)
        p.hosted_on(host, wall)
        p.in_assembly(host, wall, 0)
        p.bounds(wall, host, 0)
        p.in_room(wall, host, 0)
        p.connects_to(wall, host, system)

        p.add_scene_view(
            SceneView(0, "Level / Class", True, [SceneViewKey.rel(Rel.ON_LEVEL)])
        )
        p.add_camera_view(
            CameraView(
                0, "Front", True, 0, 0, -10, 2, 0, 1, 0, 0, 0, 1, units="m", fov=45
            )
        )
        p.add_model_placement(
            "projectBasePoint",
            PLACEMENT,
            "m",
            True,
            source="projectBasePoint",
            options={"internalOrigin": IDENTITY, "projectBasePoint": PLACEMENT},
        )
        p.add_model_property("projectInformation.name", "Fixture")
        p.add_property_set_definition(
            "Pset_Wall", "pset-key", "Width", "bucket-w", "double", unit="mm"
        )
        p.add_property_set_definition(
            "Pset_Wall", "pset-key", "LoadBearing", "bucket-lb", "boolean"
        )

    return Ks(
        wall=wall,
        member=member,
        placed=placed,
        nested_member=nested_member,
        inner_member=inner_member,
        host=host,
        mesh_geo=mesh_geo,
        region_geo=region_geo,
        text_geo=text_geo,
        definition=definition,
        inner_definition=inner_definition,
        instance=instance,
        nested_instance=nested_instance,
        material=material,
        color=color,
        level=level,
        layer=layer,
        model=model,
        system=system,
        system2=system2,
        group=group,
    )
