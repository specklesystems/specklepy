import os

import pytest

from specklepy.bundle.bundle_reader import read_bundle
from specklepy.bundle.model import Model
from specklepy.objects.data_objects import DataObject
from specklepy.objects.geometry import Region
from specklepy.objects.models.collections.collection import Collection
from specklepy.objects.proxies import InstanceProxy
from tests.bundle import fixture_bundle


def _flatten(collection: Collection) -> list:
    out = []
    for e in collection.elements:
        out.append(e)
        if isinstance(e, Collection):
            out.extend(_flatten(e))
    return out


@pytest.fixture
def root(tmp_path):
    out = str(tmp_path)
    ks = fixture_bundle.build(out, "fx")
    files = sorted(os.path.join(out, f) for f in os.listdir(out))
    return Model("p", "m", "v", out, files, read_bundle(out)).to_base(), ks


def test_root_shape(root):
    tree, _ = root
    assert isinstance(tree, Collection)
    assert (tree.name, tree.applicationId, tree.id) == (
        "Received model",
        "artifact-root",
        "artifact-root",
    )
    assert tree["version"] == 4 and tree["units"] == ""
    containers = [e for e in tree.elements if isinstance(e, Collection)]
    assert sorted(c.name for c in containers) == [
        "Group A",
        "Host",
        "Hot Water",
        "Walls",
    ]
    assert all(c.applicationId == c.id and c.id.startswith("coll-") for c in containers)


def test_objects_are_data_objects_keyed_by_application_id(root):
    tree, _ = root
    by_id = {e.applicationId: e for e in _flatten(tree)}
    wall = by_id["wall-1"]
    assert isinstance(wall, DataObject) and wall.id == "wall-1"
    assert wall.name == "Wall-1"
    assert wall.properties == {"Pset_Wall": {"Width": 200.0, "LoadBearing": True}}
    assert [type(g).__name__ for g in wall.displayValue] == ["Mesh", "Region", "Text"]
    assert all(g.applicationId == "wall-1" for g in wall.displayValue)
    assert isinstance(wall.displayValue[1], Region)
    walls = next(c for c in tree.elements if getattr(c, "name", None) == "Walls")
    assert walls.elements == [wall]
    assert "host-1" not in by_id  # no display geometry → skipped
    assert "member-1" not in by_id  # definition member without a render edge


def test_placements_become_instance_proxies(root):
    tree, ks = root
    by_id = {e.applicationId: e for e in _flatten(tree)}
    placed = by_id["placed-1"]
    assert isinstance(placed, InstanceProxy)
    assert placed.definitionId == f"def-{ks.definition}"
    assert placed.transform == fixture_bundle.IDENTITY and placed.units == "m"
    nested = by_id[f"nested-inst-{ks.nested_instance}"]
    assert isinstance(nested, InstanceProxy)
    assert nested.definitionId == f"def-{ks.inner_definition}"


def test_material_and_definition_proxies(root):
    tree, ks = root
    [material] = tree["renderMaterialProxies"]
    assert (
        material.value.name == "Painted Steel" and material.value.emissive == -16711936
    )
    assert material.value["ior"] == 1.45 and material.objects == ["wall-1"]
    assert material.applicationId == f"mat-{ks.material}"

    definitions = {d.applicationId: d for d in tree["instanceDefinitionProxies"]}
    outer = definitions[f"def-{ks.definition}"]
    assert outer.name == "WallBody" and outer.maxDepth == 0
    assert outer.objects == [
        f"def-geo-{ks.mesh_geo + 3}",
        f"nested-inst-{ks.nested_instance}",
    ]
    inner = definitions[f"def-{ks.inner_definition}"]
    assert inner.name == "Bolt" and inner.maxDepth == 1
    assert inner.objects == [f"def-geo-{ks.mesh_geo + 4}"]
    synthesized = {e.applicationId: e for e in tree.elements}[
        f"def-geo-{ks.mesh_geo + 3}"
    ]
    assert isinstance(synthesized, DataObject) and synthesized.properties == {}


def test_reference_point_is_the_inverse_placement_in_feet(root):
    tree, _ = root
    matrix = tree["referencePointTransform"]["transform"]
    assert matrix[:12] == [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    assert matrix[12] == pytest.approx(-30.5 / 0.3048)
    assert matrix[13] == pytest.approx(-12.2 / 0.3048)
    assert matrix[14] == pytest.approx(0.0) and matrix[15] == 1.0
