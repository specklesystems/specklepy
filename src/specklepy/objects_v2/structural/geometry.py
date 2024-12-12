from enum import Enum
from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry import Line, Mesh, Plane, Point, Vector
from specklepy.objects.structural.axis import Axis
from specklepy.objects.structural.properties import (
    Property1D,
    Property2D,
    Property3D,
    PropertyDamper,
    PropertyMass,
    PropertySpring,
)

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
    code: Optional[str] = None
    stiffnessX: float = 0.0
    stiffnessY: float = 0.0
    stiffnessZ: float = 0.0
    stiffnessXX: float = 0.0
    stiffnessYY: float = 0.0
    stiffnessZZ: float = 0.0


class Node(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Node"):
    name: Optional[str] = None
    basePoint: Optional[Point] = None
    constraintAxis: Optional[Axis] = None
    restraint: Optional[Restraint] = None
    springProperty: Optional[PropertySpring] = None
    massProperty: Optional[PropertyMass] = None
    damperProperty: Optional[PropertyDamper] = None


class Element1D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element1D"):
    name: Optional[str] = None
    baseLine: Optional[Line] = None
    property: Optional[Property1D] = None
    type: Optional[ElementType1D] = None
    end1Releases: Optional[Restraint] = None
    end2Releases: Optional[Restraint] = None
    end1Offset: Optional[Vector] = None
    end2Offset: Optional[Vector] = None
    orientationNode: Optional[Node] = None
    orinetationAngle: float = 0.0
    localAxis: Optional[Plane] = None
    parent: Optional[Base] = None
    end1Node: Optional[Node] = None
    end2Node: Optional[Node] = None
    topology: Optional[List] = None
    displayMesh: Optional[Mesh] = None


class Element2D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element2D"):
    name: Optional[str] = None
    property: Optional[Property2D] = None
    type: Optional[ElementType2D] = None
    offset: float = 0.0
    orientationAngle: float = 0.0
    parent: Optional[Base] = None
    topology: Optional[List] = None
    displayMesh: Optional[Mesh] = None


class Element3D(Base, speckle_type=STRUCTURAL_GEOMETRY + ".Element3D"):
    name: Optional[str] = None
    baseMesh: Optional[Mesh] = None
    property: Optional[Property3D] = None
    type: Optional[ElementType3D] = None
    orientationAngle: float = 0.0
    parent: Optional[Base] = None
    topology: List


# class Storey needs ependency on built elements first
