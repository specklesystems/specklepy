"""Build hook: pull the generated bundle-spec Python target from the sibling checkout.

Mirrors speckle-sharp-sdk, whose csproj compiles
``../../../speckle-bundle-spec/generated/csharp/*.cs`` straight from an adjacent clone:
the spec is never copied into this repo by hand. On every build (wheel, sdist, and the
editable install ``uv sync`` performs) the three generated modules are copied from
``<spec>/generated/python/`` into ``src/specklepy/bundle/spec/`` — gitignored there — so
the published wheel carries the constants and a dev checkout imports them unchanged.

``<spec>`` is ``$SPECKLE_BUNDLE_SPEC_DIR`` if set, else ``../speckle-bundle-spec`` next
to this repo. CI provisions it with ``.github/actions/checkout-bundle-spec`` (the pinned
SHA there is the ONE place the spec version is pinned for this repo). A missing checkout
is a hard build error, never a silent fallback to a stale copy (ADR-0004: fail loud).

The hook runs when specklepy is (re)built: after moving the spec checkout to a new
commit, run ``mise run install`` (``uv sync --reinstall-package specklepy``) so the
editable install picks up the new modules.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

GENERATED = ("bundle_spec.py", "bundle_schemas.py", "bundle_cols.py")


class BundleSpecHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:  # noqa: ARG002
        root = Path(self.root)
        dst = root / "src" / "specklepy" / "bundle" / "spec"
        # Building from an unpacked sdist (PKG-INFO present — `uv build`'s wheel step,
        # or `pip install specklepy-x.tar.gz`): the sdist already ships the modules
        # copied in when it was made; there is no sibling checkout to consult.
        if (root / "PKG-INFO").is_file():
            missing = [f for f in GENERATED if not (dst / f).is_file()]
            if missing:
                raise RuntimeError(
                    "sdist is missing generated bundle-spec modules: "
                    + ", ".join(missing)
                )
            return
        override = os.environ.get("SPECKLE_BUNDLE_SPEC_DIR")
        spec_dir = Path(override) if override else root.parent / "speckle-bundle-spec"
        src = spec_dir / "generated" / "python"
        missing = [f for f in GENERATED if not (src / f).is_file()]
        if missing:
            raise RuntimeError(
                "speckle-bundle-spec generated Python target not found: "
                f"{src} lacks {', '.join(missing)}. "
                "specklepy builds against a sibling clone of "
                "https://github.com/specklesystems/speckle-bundle-spec (like "
                "speckle-sharp-sdk). Clone it next to this repo, or point "
                "SPECKLE_BUNDLE_SPEC_DIR at a checkout."
            )
        for f in GENERATED:
            shutil.copyfile(src / f, dst / f)
        self.app.display_info(f"bundle-spec: copied {', '.join(GENERATED)} from {src}")
