from enum import Enum

from ..base import Base


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


class Material(Base, speckle_type=STRUCTURAL_MATERIALS):
    name: str = None
    grade: str = None
    materialType: MaterialType = None
    designCode: str = None
    codeYear: str = None
    strength: float = 0.0
    elasticModulus: float = 0.0
    poissonsRatio: float = 0.0
    shearModulus: float = 0.0
    density: float = 0.0
    thermalExpansivity: float = 0.0
    dampingRatio: float = 0.0
    cost: float = 0.0
    materialSafetyFactor: float = 0.0


class Concrete(Material, speckle_type=STRUCTURAL_MATERIALS + ".Concrete"):
    compressiveStrength: float = 0.0
    tensileStrength: float = 0.0
    flexuralStrength: float = 0.0
    maxCompressiveStrength: float = 0.0
    maxTensileStrength: float = 0.0
    maxAggregateSize: float = 0.0
    lightweight: bool = None


class Steel(Material, speckle_type=STRUCTURAL_MATERIALS + ".Steel"):
    yieldStrength: float = 0.0
    ultimateStrength: float = 0.0
    maxStrain: float = 0.0
    strainHardeningModulus: float = 0.0


class Timber(Material, speckle_type=STRUCTURAL_MATERIALS + ".Timber"):
    species: str = None
