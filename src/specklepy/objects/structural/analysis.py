from typing import List, Optional

from specklepy.objects.base import Base

STRUCTURAL_ANALYSIS = "Objects.Structural.Analysis."


class ModelUnits(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelUnits"):
    length: Optional[str] = None
    sections: Optional[str] = None
    displacements: Optional[str] = None
    stress: Optional[str] = None
    force: Optional[str] = None
    mass: Optional[str] = None
    time: Optional[str] = None
    temperature: Optional[str] = None
    velocity: Optional[str] = None
    acceleration: Optional[str] = None
    energy: Optional[str] = None
    angle: Optional[str] = None
    strain: Optional[str] = None


class ModelSettings(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelSettings"):
    modelUnits: Optional[ModelUnits] = None
    steelCode: Optional[str] = None
    concreteCode: Optional[str] = None
    coincidenceTolerance: float = 0.0


class ModelInfo(Base, speckle_type=STRUCTURAL_ANALYSIS + "ModelInfo"):
    name: Optional[str] = None
    description: Optional[str] = None
    projectNumber: Optional[str] = None
    projectName: Optional[str] = None
    settings: Optional[ModelSettings] = None
    initials: Optional[str] = None
    application: Optional[str] = None


class Model(Base, speckle_type=STRUCTURAL_ANALYSIS + "Model"):
    specs: Optional[ModelInfo] = None
    nodes: Optional[List] = None
    elements: Optional[List] = None
    loads: Optional[List] = None
    restraints: Optional[List] = None
    properties: Optional[List] = None
    materials: Optional[List] = None
    layerDescription: Optional[str] = None
