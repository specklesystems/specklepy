from enum import Enum
from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry import Vector
from specklepy.objects.structural.axis import Axis

STRUCTURAL_LOADING = "Objects.Structural.Loading."


class LoadType(int, Enum):
    none = 0
    Dead = 1
    SuperDead = 2
    Soil = 3
    Live = 4
    LiveRoof = 5
    ReducibleLive = 6
    Wind = 7
    Snow = 8
    Rain = 9
    Thermal = 10
    Notional = 11
    Prestress = 12
    Equivalent = 13
    Accidental = 14
    SeismicRSA = 15
    SeismicAccTorsion = 16
    SeismicStatic = 17
    Other = 18


class ActionType(int, Enum):
    none = 0
    Permanent = 1
    Variable = 2
    Accidental = 3


class BeamLoadType(int, Enum):
    Point = 0
    Uniform = 1
    Linear = 2
    Patch = 3
    TriLinear = 4


class FaceLoadType(int, Enum):
    Constant = 0
    Variable = 1
    Point = 2


class LoadDirection2D(int, Enum):
    X = 0
    Y = 1
    Z = 2


class LoadDirection(int, Enum):
    X = 0
    Y = 1
    Z = 2
    XX = 3
    YY = 4
    ZZ = 5


class LoadAxisType(int, Enum):
    Global = 0
    Local = 1  # local element axes
    DeformedLocal = (
        2  # element local axis that is embedded in the element as it deforms
    )


class CombinationType(int, Enum):
    LinearAdd = 0
    Envelope = 1
    AbsoluteAdd = 2
    SRSS = 3
    RangeAdd = 4


class LoadCase(Base, speckle_type=STRUCTURAL_LOADING + "LoadCase"):
    name: Optional[str] = None
    loadType: Optional[LoadType] = None
    group: Optional[str] = None
    actionType: Optional[ActionType] = None
    description: Optional[str] = None


class Load(Base, speckle_type=STRUCTURAL_LOADING + "Load"):
    name: Optional[str] = None
    loadCase: Optional[LoadCase] = None


class LoadBeam(Load, speckle_type=STRUCTURAL_LOADING + "LoadBeam"):
    elements: Optional[List] = None
    loadType: Optional[BeamLoadType] = None
    direction: Optional[LoadDirection] = None
    loadAxis: Optional[Axis] = None
    loadAxisType: Optional[LoadAxisType] = None
    isProjected: Optional[bool] = None
    values: Optional[List] = None
    positions: Optional[List] = None


class LoadCombinations(Base, speckle_type=STRUCTURAL_LOADING + "LoadCombination"):
    name: Optional[str] = None
    loadCases: List
    loadFactors: List
    combinationType: CombinationType


class LoadFace(Load, speckle_type=STRUCTURAL_LOADING + "LoadFace"):
    elements: Optional[List] = None
    loadType: Optional[FaceLoadType] = None
    direction: Optional[LoadDirection2D] = None
    loadAxis: Optional[Axis] = None
    loadAxisType: Optional[LoadAxisType] = None
    isProjected: Optional[bool] = None
    values: Optional[List] = None
    positions: Optional[List] = None


class LoadGravity(Load, speckle_type=STRUCTURAL_LOADING + "LoadGravity"):
    elements: Optional[List] = None
    nodes: Optional[List] = None
    gravityFactors: Optional[Vector] = None


class LoadNode(Load, speckle_type=STRUCTURAL_LOADING + "LoadNode"):
    nodes: Optional[List] = None
    loadAxis: Optional[Axis] = None
    direction: Optional[LoadDirection] = None
    value: float = 0.0
