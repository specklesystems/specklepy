"""Speckle 4.0 bundle producer (eav + envelope + geometries parquet).

Optional feature — requires ``specklepy[bundle]`` (pyarrow). The vocabulary and
parquet schemas are sourced from the generated, vendored
:mod:`specklepy.bundle.spec` (single source of truth: the ``speckle-bundle-spec``
repo). The typed producer API is
:class:`~specklepy.bundle.pipeline.ObjectsArtifactPipeline`; upload via
:class:`~specklepy.bundle.upload.ArtifactPipeline`.

Geometry blobs are encoded and decoded by :mod:`specklepy.bundle.sgeo`
(``sgeo.encode`` / ``sgeo.decode``), which receivers use to read a downloaded
bundle back. Decoding covers every primitive the encoder emits.
"""

from specklepy.bundle.builder import BundleBuilder, BundleFiles
from specklepy.bundle.envelope_writer import (
    CameraView,
    Producer,
    SceneView,
    SceneViewKey,
)
from specklepy.bundle.model import Model, ModelGeometry, ModelObject
from specklepy.bundle.pipeline import ObjectsArtifactPipeline
from specklepy.bundle.receive import receive
from specklepy.bundle.send import SendOptions, SendResult, send
from specklepy.bundle.spec import SCHEMA_VERSION, NodeKind, Rel
from specklepy.bundle.upload import ArtifactPipeline

__all__ = [
    "ObjectsArtifactPipeline",
    "ArtifactPipeline",
    "receive",
    "send",
    "SendOptions",
    "SendResult",
    "BundleBuilder",
    "BundleFiles",
    "Model",
    "ModelObject",
    "ModelGeometry",
    "receive",
    "send",
    "SendOptions",
    "SendResult",
    "BundleBuilder",
    "BundleFiles",
    "Model",
    "ModelObject",
    "ModelGeometry",
    "Producer",
    "SceneView",
    "SceneViewKey",
    "CameraView",
    "NodeKind",
    "Rel",
    "SCHEMA_VERSION",
]
