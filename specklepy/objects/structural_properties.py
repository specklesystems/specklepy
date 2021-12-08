from enum import Enum
from typing import Any, List, Optional

from structural_geometry import Axis

from .base import Base
from .encoding import CurveArray, CurveTypeEncoding, ObjectArray
from .units import get_encoding_from_units, get_units_from_encoding

from .structural_material import *


STRUCTURAL_PROPERTY = "Objectives.Structural.Properties"


class Property(Base, speckle_type = STRUCTURAL_PROPERTY):
    name: str = None

class Property1D(Property, speckle_type = STRUCTURAL_PROPERTY + ".Property1D"):
    MemberType:str = None
    Material: Material = None
    SectionProfile: SectionProfile = None
    BaseReferencePoint:  str = None
    offsetY: float = 0.0
    offsetZ: float = 0.0

class Property2D(Property, speckle_type = STRUCTURAL_PROPERTY + ".Property2D"):
    PropertyType2D : str = None
    thickness: float = 0.0
    Material:  Material = None
    axis : Axis = None
    referenceSurface : str = None
    zOffset : float = 0.0
    modifierInPlane : float = 0.0
    modifierBending : float = 0.0
    modifierShear : float = 0.0
    modifierVolume : float =0.0

class Property3D(Property, speckle_type = STRUCTURAL_PROPERTY + ".Property3D"):
    PropertyType3D : str = None
    Material: Material = None
    axis : Axis = None

class PropertyDamper(Property,speckle_type = STRUCTURAL_PROPERTY + ".PropertyDamper"):
    damperType : str = None
    dampingX: float = 0.0
    dampingY: float = 0.0
    dampingZ: float = 0.0
    dampingXX: float = 0.0
    dampingYY: float = 0.0
    dampingZZ: float = 0.0

class PropertyMass(Property, speckle_type = STRUCTURAL_PROPERTY + ".PropertyMass"):
    mass : float = 0.0
    inertiaXX :  float = 0.0
    inertiaYY : float  = 0.0
    inertiaZZ : float = 0.0
    inertiaXY : float = 0.0
    inertiaYZ : float = 0.0 
    inertiaZX : float = 0.0
    massModified : bool = None
    massModifierX : float = 0.0
    massModifierY : float = 0.0
    massModifierZ : float = 0.0

class PropertySpring(Property, speckle_type = STRUCTURAL_PROPERTY + ".PropertySpring"):
    springCurveX : float = 0.0
    stiffnessX : float  = 0.0
    springCurveY : float  = 0.0
    stiffnessY : float = 0.0
    springCurveZ : float  = 0.0
    stiffnessZ : float = 0.0 
    springCurveXX : float  = 0.0 
    stiffnessXX : float = 0.0
    springCurveYY : float = 0.0 
    stiffnessYY : float  = 0.0
    springCurveZZ : float = 0.0
    stiffnessZZ : float = 0.0
    dampingRatio : float = 0.0
    dampingX : float = 0.0
    dampingY : float = 0.0
    dampingZ : float = 0.0
    dampingXX : float = 0.0 
    dampingYY : float = 0.0
    dampingZZ : float =  0.0 
    matrix : float = 0.0
    postiveLockup : float = 0.0
    frictionCoefficient : float = 0.0

class SectionProfile(Base, speckle_type = STRUCTURAL_PROPERTY + ".SectionProfile"):
    name: str = None
    shapeType:str =  None
    area: float = 0.0
    Iyy: float = 0.0
    Izz: float = 0.0
    J:float = 0.0
    Ky: float = 0.0
    weight: float = 0.0
    units: str = None 


class ReferenceSurfaceEnum(int, Enum):
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

class memberTypeEnum(int, Enum):
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

class shapeType(int, Enum):
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