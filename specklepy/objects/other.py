from .base import Base

OTHER = "Objects.Other."


class RenderMaterial(Base, speckle_type=OTHER + "RenderMaterial"):
    name: str = None
    opacity: float = 1
    metalness: float = 0
    roughness: float = 1
    diffuse: int = -2894893  # light gray arbg
    emissive: int = -16777216  # black arbg
