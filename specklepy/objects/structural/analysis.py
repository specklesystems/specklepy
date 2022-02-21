from typing import List

from ..base import Base
from ..geometry import *
from .properties import *

STRUCTURAL_ANALYSIS = "Objects.Structural.Analysis."


class ModelUnits(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelUnits"):
    length: str = None
    sections: str = None
    displacements: str = None
    stress: str = None
    force: str = None
    mass: str = None
    time: str = None
    temperature: str = None
    velocity: str = None
    acceleration: str = None
    energy: str = None
    angle: str = None
    strain: str = None


class ModelSettings(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelSettings"):
    modelUnits: ModelUnits = None
    steelCode: str = None
    concreteCode: str = None
    coincidenceTolerance: float = 0.0


class ModelInfo(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelInfo"):
    name: str = None
    description: str = None
    projectNumber: str = None
    projectName: str = None
    settings: ModelSettings = None
    initials: str = None
    application: str = None


class Model(Base, speckle_type=STRUCTURAL_ANALYSIS + "Model"):
    specs: ModelInfo = None
    nodes: List = None
    elements: List = None
    loads: List = None
    restraints: List = None
    properties: List = None
    materials: List = None
    layerDescription: str = None
