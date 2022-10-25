from enum import Enum
from typing import List

from ..base import Base
from ..geometry import *
from .properties import *
from .axis import Axis

STRUCTURAL_GEOMETRY = "Objects.Structural.Geometry"


class ElementType1D(int, Enum):
    Beam = 0
    Brace = 1
    Bar = 2
    Column = 3
    Rod = 4
    Spring = 5
    Tie = 6
    Strut = 7
    Link = 8
    Damper = 9
    Cable = 10
    Spacer = 11
    Other = 12
    Null = 13


class ElementType2D(int, Enum):
    Quad4 = 0
    Quad8 = 1
    Triangle3 = 2
    Triangle6 = 3


class ElementType3D(int, Enum):
    Brick8 = 0
    Wedge6 = 1
    Pyramid5 = 2
    Tetra4 = 3


class Restraint(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Restraint"):
    code: str = None
    stiffnessX: float = 0.0
    stiffnessY: float = 0.0
    stiffnessZ: float = 0.0
    stiffnessXX: float = 0.0
    stiffnessYY: float = 0.0
    stiffnessZZ: float = 0.0
    units: str = None


class Node(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Node"):
    name: str = None
    basePoint: Point = None
    constraintAxis: Axis = None
    restraint: Restraint = None
    springProperty: PropertySpring = None
    massProperty: PropertyMass = None
    damperProperty: PropertyDamper = None
    units: str = None


class Element1D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element1D"):
    name: str = None
    baseLine: Line = None
    property: Property1D = None
    type: ElementType1D = None
    end1Releases: Restraint = None
    end2Releases: Restraint = None
    end1Offset: Vector = None
    end2Offset: Vector = None
    orientationNode: Node = None
    orinetationAngle: float = 0.0
    localAxis: Plane = None
    parent: Base = None
    end1Node: Node = Node
    end2Node: Node = Node
    topology: List = None
    displayMesh: Mesh = None
    units: str = None


class Element2D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element2D"):
    name: str = None
    property: Property2D = None
    type: ElementType2D = None
    offset: float = 0.0
    orientationAngle: float = 0.0
    parent: Base = None
    topology: List = None
    displayMesh: Mesh = None
    units: str = None


class Element3D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element3D"):
    name: str = None
    baseMesh: Mesh = None
    property: Property3D = None
    type: ElementType3D = None
    orientationAngle: float = 0.0
    parent: Base = None
    topology: List
    units: str = None


# class Storey needs ependency on built elements first
