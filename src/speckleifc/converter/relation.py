"""Relation-only sweeps (the ``relations`` namespace): passes whose sole output is
edges between already-interned objects — port connectivity, void/fill hosting and
space boundaries. Membership edges (IN_SYSTEM, IN_GROUP, ON_LEVEL, …) are emitted by
their owning managers in :mod:`speckleifc.converter.node`."""

from __future__ import annotations

import logging

from ifcopenshell.entity_instance import entity_instance
from ifcopenshell.geom import file

from specklepy.bundle.builder import BundleBuilder

logger = logging.getLogger(__name__)


def emit_connections(ifc_file: file, builder: BundleBuilder) -> None:
    for rel in ifc_file.by_type("IfcRelConnectsPorts"):
        source = _owner_of_port(rel.RelatingPort)
        target = _owner_of_port(rel.RelatedPort)
        if source is None or target is None:
            continue
        source_id = getattr(source, "GlobalId", None)
        target_id = getattr(target, "GlobalId", None)
        if not source_id or not target_id:
            continue
        source_obj = builder.get_or_add_object(source_id)
        target_obj = builder.get_or_add_object(target_id)
        src_flow = getattr(rel.RelatingPort, "FlowDirection", None)
        tgt_flow = getattr(rel.RelatedPort, "FlowDirection", None)
        # SOURCE→SINK is directed; anything else is undirected → reciprocal pair
        if src_flow == "SOURCE" and tgt_flow == "SINK":
            source_obj.connect_to(target_obj)
        elif src_flow == "SINK" and tgt_flow == "SOURCE":
            target_obj.connect_to(source_obj)
        else:
            source_obj.connect_to(target_obj)
            target_obj.connect_to(source_obj)


def emit_hosting(ifc_file: file, builder: BundleBuilder) -> None:
    for rel in ifc_file.by_type("IfcRelFillsElement"):
        opening = rel.RelatingOpeningElement
        filler = rel.RelatedBuildingElement
        if opening is None or filler is None:
            continue
        host = next(
            (
                v.RelatingBuildingElement
                for v in getattr(opening, "VoidsElements", None) or []
                if v.RelatingBuildingElement is not None
            ),
            None,
        )
        if host is None:
            continue
        filler_obj = builder.try_get_object(getattr(filler, "GlobalId", None) or "")
        host_obj = builder.try_get_object(getattr(host, "GlobalId", None) or "")
        if filler_obj is None or host_obj is None:
            logger.debug(
                "Fill/void pair %s → %s not fully converted; skipping HOSTED_ON",
                getattr(filler, "GlobalId", None),
                getattr(host, "GlobalId", None),
            )
            continue
        if filler_obj.host is None:
            filler_obj.host = host_obj


def emit_space_boundaries(ifc_file: file, builder: BundleBuilder) -> None:
    emitted: set[tuple[int, int]] = set()
    for rel in ifc_file.by_type("IfcRelSpaceBoundary"):
        space = getattr(rel, "RelatingSpace", None)
        element = getattr(rel, "RelatedBuildingElement", None)
        if space is None or element is None:  # virtual boundary
            continue
        space_obj = builder.try_get_object(getattr(space, "GlobalId", None) or "")
        element_obj = builder.try_get_object(getattr(element, "GlobalId", None) or "")
        if space_obj is None or element_obj is None:
            logger.debug(
                "Space boundary %s not fully converted; skipping BOUNDS",
                getattr(rel, "GlobalId", None),
            )
            continue
        if (element_obj.k, space_obj.k) not in emitted:
            emitted.add((element_obj.k, space_obj.k))
            element_obj.bounds(space_obj)


def _owner_of_port(port: entity_instance | None) -> entity_instance | None:
    if port is None:
        return None
    # IFC4: port nested under its element via IfcRelNests (inverse: Nests)
    for rel in getattr(port, "Nests", None) or []:
        if rel.RelatingObject is not None:
            return rel.RelatingObject
    # Legacy: IfcRelConnectsPortToElement (inverse: ContainedIn)
    for rel in getattr(port, "ContainedIn", None) or []:
        if getattr(rel, "RelatedElement", None) is not None:
            return rel.RelatedElement
    return None
