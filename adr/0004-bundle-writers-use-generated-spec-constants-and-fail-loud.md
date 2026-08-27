# ADR-0004: Bundle writers address columns via generated spec constants; any dropped row fails the job

- **Status**: pointer — the canonical text lives in the speckle-atlas layer:
  [`atlas/adr/0004`](../../atlas/adr/0004-bundle-writers-use-generated-spec-constants-and-fail-loud.md)
  (standing stack ADR, no owning spec)
- **Date**: 2026-08-04

Summary: after the 2026-08 empty-`envelope.nodes` incident (a bundle-spec
column insert drifted from the C++ writers' hand-written ordinals; six days
of green jobs shipping viewer-blank versions — this repo's vendored spec
was itself stale, missing the new columns), the stack rule is: bundle
writers address columns **only** via the spec's generated column-index
constants — a hand-written ordinal or positional argument into a
spec-defined shape is a defect; writes are type-checked and any dropped row
fails the job loudly; relations referencing missing/empty nodes are a hard
error in the spec validator; and CI round-trips each writer against its
pinned spec on every PR.

## What this binds in this repo

- **`src/specklepy/bundle/`** (`parquet_table_writer.py`,
  `envelope_writer.py`, `eav_writer.py`, `geometries_writer.py`): row-arity
  guards raise with clear errors; material params are keyword-only so
  positional drift is impossible (#506).
- **`src/specklepy/bundle/spec/`**: the generated schemas/constants are no
  longer vendored — `hatch_build.py` copies them from the sibling
  `../speckle-bundle-spec` checkout on every build (the spec SHA CI builds
  against is pinned once in `.github/actions/checkout-bundle-spec/action.yml`),
  so a stale copy — this repo's version of ordinal drift (#506 re-synced the
  old vendor copy after it went stale ahead of the incident) — can no longer
  happen silently: a missing checkout fails the build.
