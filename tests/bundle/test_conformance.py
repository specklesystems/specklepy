"""Emits the full fixture bundle and, when a speckle-bundle-spec checkout is available,
runs its validator against it (ADR-0004 layer 4).

Set ``SPECKLE_BUNDLE_SPEC_DIR`` to the checkout; ``SPECKLE_BUNDLE_FIXTURE_DIR`` to keep
the emitted bundle at a fixed path.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from tests.bundle import fixture_bundle

BASE = "fixture"


def _fixture_dir(tmp_path) -> str:
    keep = os.environ.get("SPECKLE_BUNDLE_FIXTURE_DIR")
    if keep:
        os.makedirs(keep, exist_ok=True)
        return keep
    return str(tmp_path)


def test_emit_fixture_bundle(tmp_path):
    out = _fixture_dir(tmp_path)
    fixture_bundle.build(out, BASE)
    assert os.path.exists(os.path.join(out, f"{BASE}.envelope.meta.parquet"))


def test_bundle_passes_spec_validator(tmp_path):
    spec_dir = os.environ.get("SPECKLE_BUNDLE_SPEC_DIR")
    if not spec_dir:
        pytest.skip("SPECKLE_BUNDLE_SPEC_DIR not set")
    if (
        shutil.which("node") is None
        or shutil.which(os.environ.get("DUCKDB_BIN", "duckdb")) is None
    ):
        pytest.skip("node and the duckdb CLI are required")

    out = _fixture_dir(tmp_path)
    fixture_bundle.build(out, BASE)
    result = subprocess.run(
        ["node", os.path.join(spec_dir, "validator", "validate-bundle.mjs"), out],
        capture_output=True,
        text=True,
        cwd=spec_dir,
    )
    assert result.returncode == 0, result.stdout + result.stderr
