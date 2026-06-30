"""Speckle 4.0 bundle producer (eav + envelope + geometries parquet).

Optional feature — requires ``specklepy[bundle]`` (pyarrow). The vocabulary and parquet
schemas are sourced from the generated, vendored :mod:`specklepy.bundle.spec` (single source
of truth: the ``speckle-bundle-spec`` repo). The typed producer API is
:class:`~specklepy.bundle.pipeline.ObjectsArtifactPipeline`; upload via
:class:`~specklepy.bundle.upload.ArtifactPipeline`.
"""

from specklepy.bundle.pipeline import ObjectsArtifactPipeline
from specklepy.bundle.spec import SCHEMA_VERSION, NodeKind, Rel
from specklepy.bundle.upload import ArtifactPipeline

__all__ = [
    "ObjectsArtifactPipeline",
    "ArtifactPipeline",
    "NodeKind",
    "Rel",
    "SCHEMA_VERSION",
]
