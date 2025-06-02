from dataclasses import dataclass

from specklepy.objects.base import Base


@dataclass(kw_only=True)
class RenderMaterial(
    Base,
    speckle_type="Objects.Other.RenderMaterial",
):
    """
    Minimal physically based material DTO class. Based on references from
    https://threejs.org/docs/index.html#api/en/materials/MeshStandardMaterial
    """

    name: str
    opacity: float = 1.0
    metalness: float = 0.0
    roughness: float = 1.0
    diffuse: int  # ARGB color as int
    emissive: int = 0  # ARGB color as int, defaults to black
