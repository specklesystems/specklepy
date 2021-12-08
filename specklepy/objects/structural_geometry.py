from enum import Enum
import enum
from typing import Any, List, Optional

from .base import Base
from .encoding import CurveArray, CurveTypeEncoding, ObjectArray
from .units import get_encoding_from_units, get_units_from_encoding
from .geometry import *
from .structural_properties import *

STRUCTURAL_GEOMETRY = "Objects.Structural.Geometry"

class Restraint (Base, speckle_type = STRUCTURAL_GEOMETRY + ".Restraint"):
    code : str = None
    stiffnessX : float  = 0.0
    stiffnessY : float = 0.0
    stiffnessZ : float = 0.0
    stiffnessXX : float = 0.0
    stiffnessYY : float = 0.0
    stiffnessZZ : float = 0.0 
    units : str = None

class Node (Base, speckle_type = STRUCTURAL_GEOMETRY + ".Node"):
    name : str = None
    basePoint : Point = None
    constraintAxis : Axis = None
    restraint : Restraint = None
    springProperty : PropertySpring = None
    massProperty : PropertyMass = None
    damperProperty : PropertyDamper = None
    units : str = None


class Element1D(Base, speckle_type =  STRUCTURAL_GEOMETRY + ".Element1D"):
    name: str= None
    baseLine : Line = None
    property : Property1D = None
    type : str =  None
    end1Releases : Restraint  = None
    end2Releases : Restraint = None
    end1Offset : Vector  = None
    end2Offset : Vector = None
    orientationNode : Node = None
    orinetationAngle : float = 0.0
    localAxis : Plane = None
    parent:  Base = None
    end1Node : Node = Node
    end2Node : Node = Node
    topology : List = None
    displayMesh : Mesh = None
    units : str = None

class Element2D (Base , speckle_type = STRUCTURAL_GEOMETRY + ".Element2D"):
    name: str = None
    property : Property2D = None
    type : str = None
    offset: float = 0.0
    orientationAngle : float = 0.0
    parent : Base  = None
    topology : List = None
    displayMesh : Mesh = None
    units : str = None

class Element3D(Base, speckle_type = STRUCTURAL_GEOMETRY + ".Element3D"):
    name : str = None
    baseMesh : Mesh = None
    property : Property3D  = None
    type : None
    orientationAngle : float = 0.0
    parent : Base  = None
    topology : List
    units : str = None

#class Storey needs ependency on built elements first

class Axis(Base, speckle_type = STRUCTURAL_GEOMETRY + ".Axis"):
    name: str = None
    axisType: str = None
    plane: Plane = None


