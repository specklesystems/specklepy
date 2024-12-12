from enum import Enum
from typing import Optional

from specklepy.objects.base import Base

STRUCTURAL_MATERIALS = "Objects.Structural.Materials"


class MaterialType(int, Enum):
    Concrete = 0
    Steel = 1
    Timber = 2
    Aluminium = 3
    Masonry = 4
    FRP = 5
    Glass = 6
    Fabric = 7
    Rebar = 8
    Tendon = 9
    ColdFormed = 10
    Other = 11


class StructuralMaterial(
    Base, speckle_type=STRUCTURAL_MATERIALS + ".StructuralMaterial"
):
    name: Optional[str] = None
    grade: Optional[str] = None
    materialType: Optional[MaterialType] = None
    designCode: Optional[str] = None
    codeYear: Optional[str] = None
    strength: float = 0.0
    elasticModulus: float = 0.0
    poissonsRatio: float = 0.0
    shearModulus: float = 0.0
    density: float = 0.0
    thermalExpansivity: float = 0.0
    dampingRatio: float = 0.0
    cost: float = 0.0
    materialSafetyFactor: float = 0.0


class Concrete(StructuralMaterial):
    compressiveStrength: float = 0.0
    tensileStrength: float = 0.0
    flexuralStrength: float = 0.0
    maxCompressiveStrain: float = 0.0
    maxTensileStrain: float = 0.0
    maxAggregateSize: float = 0.0
    lightweight: Optional[bool] = None


class Steel(StructuralMaterial, speckle_type=STRUCTURAL_MATERIALS + ".Steel"):
    yieldStrength: float = 0.0
    ultimateStrength: float = 0.0
    maxStrain: float = 0.0
    strainHardeningModulus: float = 0.0


class Timber(StructuralMaterial, speckle_type=STRUCTURAL_MATERIALS + ".Timber"):
    species: Optional[str] = None
