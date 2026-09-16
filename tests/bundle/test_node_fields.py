"""The row -> per-kind projection: where a mandatory NULL stops being silent."""

from __future__ import annotations

import pytest

from specklepy.bundle import node_fields
from specklepy.bundle.bundle_reader import Node
from specklepy.bundle.spec import NodeKind


def _container(subtype: str | None) -> Node:
    return Node(
        kind=int(NodeKind.CONTAINER),
        name="Level 1",
        def_ref=None,
        transform=None,
        units=None,
        subtype=subtype,
        argb=None,
        opacity=None,
        metalness=None,
        roughness=None,
        emissive=None,
        ior=None,
        elevation=None,
        gh_topology=None,
    )


def test_container_complete_row_projects():
    fields = node_fields.container(4, _container("Layer"))

    assert fields.subtype == "Layer"
    assert fields.name == "Level 1"


def test_container_null_subtype_raises_naming_node_and_column():
    with pytest.raises(ValueError) as excinfo:
        node_fields.container(4, _container(None))

    assert "Node 4" in str(excinfo.value)
    assert "nodes.subtype" in str(excinfo.value)
