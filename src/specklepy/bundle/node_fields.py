"""Project a wide ``nodes`` row onto the per-kind record the spec declares for it.

Columns the spec marks mandatory are non-optional on those records, so a NULL is a
producer defect and fails here instead of being quietly defaulted.
"""

from __future__ import annotations

from typing import TypeVar

from specklepy.bundle.bundle_reader import Node
from specklepy.bundle.spec import (
    Color,
    Container,
    Definition,
    Instance,
    Level,
    Material,
)

T = TypeVar("T")


def _required(value: T | None, k: int, column: str) -> T:
    if value is None:
        raise ValueError(
            f"Node {k}: nodes.{column} is mandatory for this node kind in the bundle "
            f"spec, but the row has NULL."
        )
    return value


def material(k: int, node: Node) -> Material:
    return Material(
        argb=_required(node.argb, k, "argb"),
        opacity=_required(node.opacity, k, "opacity"),
        metalness=_required(node.metalness, k, "metalness"),
        roughness=_required(node.roughness, k, "roughness"),
        name=node.name,
        emissive=node.emissive,
        ior=node.ior,
    )


def color(k: int, node: Node) -> Color:
    return Color(argb=_required(node.argb, k, "argb"))


def level(k: int, node: Node) -> Level:
    return Level(elevation=_required(node.elevation, k, "elevation"), name=node.name)


def container(k: int, node: Node) -> Container:
    return Container(
        subtype=_required(node.subtype, k, "subtype"),
        name=node.name,
        def_ref=node.def_ref,
        gh_topology=node.gh_topology,
    )


def definition(k: int, node: Node) -> Definition:
    return Definition(name=node.name, def_ref=node.def_ref)


def instance(k: int, node: Node) -> Instance:
    return Instance(
        transform=_required(node.transform, k, "transform"),
        def_ref=_required(node.def_ref, k, "def_ref"),
        units=node.units,
    )
