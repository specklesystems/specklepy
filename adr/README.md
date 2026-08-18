# Architecture decision records

Repo-local ADRs and pointer stubs to stack-level decisions share one number
sequence (pointer stubs keep their atlas number and title; local ADRs
continue numbering after adopted stubs — see the speckle-atlas layer's
ADR-0003 for the pointer-stub convention). This lives outside `docs/`
because that directory is the published mkdocs site.

- [0004 — Bundle writers address columns via generated spec constants; any dropped row fails the job](0004-bundle-writers-use-generated-spec-constants-and-fail-loud.md)
  (pointer — canonical text in the atlas layer)
