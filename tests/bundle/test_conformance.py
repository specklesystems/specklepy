"""Emits bundles and, when a speckle-bundle-spec checkout is available, runs its
validator against them (ADR-0004 layer 4).

Set ``SPECKLE_BUNDLE_SPEC_DIR`` to the checkout; ``SPECKLE_BUNDLE_FIXTURE_DIR`` to keep
the emitted fixture bundle at a fixed path.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from specklepy.bundle import BundleBuilder
from tests.bundle import fixture_bundle

BASE = "fixture"


def _fixture_dir(tmp_path) -> str:
    keep = os.environ.get("SPECKLE_BUNDLE_FIXTURE_DIR")
    if keep:
        os.makedirs(keep, exist_ok=True)
        return keep
    return str(tmp_path)


def _validate(out: str) -> None:
    spec_dir = os.environ.get("SPECKLE_BUNDLE_SPEC_DIR")
    if not spec_dir:
        pytest.skip("SPECKLE_BUNDLE_SPEC_DIR not set")
    if (
        shutil.which("node") is None
        or shutil.which(os.environ.get("DUCKDB_BIN", "duckdb")) is None
    ):
        pytest.skip("node and the duckdb CLI are required")
    result = subprocess.run(
        ["node", os.path.join(spec_dir, "validator", "validate-bundle.mjs"), out],
        capture_output=True,
        text=True,
        cwd=spec_dir,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_emit_fixture_bundle(tmp_path):
    out = _fixture_dir(tmp_path)
    fixture_bundle.build(out, BASE)
    assert os.path.exists(os.path.join(out, f"{BASE}.envelope.meta.parquet"))


def test_bundle_passes_spec_validator(tmp_path):
    out = _fixture_dir(tmp_path)
    fixture_bundle.build(out, BASE)
    _validate(out)


def test_builder_bundle_passes_spec_validator(tmp_path):
    from tests.bundle.test_builder import PRODUCER, T, describe, tri

    out = str(tmp_path)
    with BundleBuilder(PRODUCER, "m", out) as b:
        layer = b.get_or_add_container_path(["Blocks"], "Layer")
        wall = describe(b, "wall", layer, {"w": 1.0}, name="Wall")
        wall.add_geometry(tri()).material = b.get_or_add_material("c", "C", -1)
        wall.color = b.get_or_add_color(-65536)
        layer.color = wall.color
        bolt = b.get_or_add_definition("bolt", "Bolt")
        bolt.add_member(describe(b, "bolt-geo", layer, {}), [tri()])
        table = b.get_or_add_definition("table", "Table")
        table.add_member(describe(b, "top", layer, {}), [tri(), tri(1)])
        table.add_member_placement(describe(b, "leg", layer, {}), bolt, T)
        describe(b, "table-1", layer, {}).place(table, T)
        describe(b, "door", layer, {}).host = wall
        b.build()
    _validate(out)
