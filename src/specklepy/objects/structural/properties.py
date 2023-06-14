from enum import Enum
from typing import Optional

from specklepy.objects.base import Base
from specklepy.objects.structural.axis import Axis
from specklepy.objects.structural.materials import StructuralMaterial

STRUCTURAL_PROPERTY = "Objects.Structural.Properties"


class MemberType(int, Enum):
    Beam = 0
    Column = 1
    Generic1D = 2
    Slab = 3
    Wall = 4
    Generic2D = 5
    VoidCutter1D = 6
    VoidCutter2D = 7


class BaseReferencePoint(int, Enum):
    Centroid = 0
    TopLeft = 1
    TopCentre = 2
    TopRight = 3
    MidLeft = 4
    MidRight = 5
    BotLeft = 6
    BotCentre = 7
    BotRight = 8


class ReferenceSurface(int, Enum):
    Top = 0
    Middle = 1
    Bottom = 2


class PropertyType2D(int, Enum):
    Stress = 0
    Fabric = 1
    Plate = 2
    Shell = 3
    Curved = 4
    Wall = 5
    Strain = 6
    Axi = 7
    Load = 8


class PropertyType3D(int, Enum):
    Solid = 0
    Infinite = 1


class ShapeType(int, Enum):
    Rectangular = 0
    Circular = 1
    I = 2  # noqa: E741
    Tee = 3
    Angle = 4
    Channel = 5
    Perimeter = 6
    Box = 7
    Catalogue = 8
    Explicit = 9
    Undefined = 10


class PropertyTypeSpring(int, Enum):
    Axial = 0
    Torsional = 1
    General = 2
    Matrix = 3
    TensionOnly = 4
    CompressionOnly = 5
    Connector = 6
    LockUp = 7
    Gap = 8
    Friction = 9


class PropertyTypeDamper(int, Enum):
    Axial = 0
    Torsional = 1
    General = 2


class Property(Base, speckle_type=STRUCTURAL_PROPERTY):
    name: Optional[str] = None


class SectionProfile(
    Base, speckle_type=STRUCTURAL_PROPERTY + ".Profiles.SectionProfile"
):
    name: Optional[str] = None
    shapeType: Optional[ShapeType] = None
    area: float = 0.0
    Iyy: float = 0.0
    Izz: float = 0.0
    J: float = 0.0
    Ky: float = 0.0
    weight: float = 0.0


class Property1D(Property, speckle_type=STRUCTURAL_PROPERTY + ".Property1D"):
    memberType: Optional[MemberType] = None
    material: Optional[StructuralMaterial] = None
    profile: Optional[SectionProfile] = None
    referencePoint: Optional[BaseReferencePoint] = None
    offsetY: float = 0.0
    offsetZ: float = 0.0


class Property2D(Property, speckle_type=STRUCTURAL_PROPERTY + ".Property2D"):
    type: Optional[PropertyType2D] = None
    thickness: float = 0.0
    material: Optional[StructuralMaterial] = None
    orientationAxis: Optional[Axis] = None
    refSurface: Optional[ReferenceSurface] = None
    zOffset: float = 0.0
    modifierInPlane: float = 0.0
    modifierBending: float = 0.0
    modifierShear: float = 0.0
    modifierVolume: float = 0.0


class Property3D(Property, speckle_type=STRUCTURAL_PROPERTY + ".Property3D"):
    type: Optional[PropertyType3D] = None
    material: Optional[StructuralMaterial] = None
    orientationAxis: Optional[Axis] = None


class PropertyDamper(Property, speckle_type=STRUCTURAL_PROPERTY + ".PropertyDamper"):
    damperType: Optional[PropertyTypeDamper] = None
    dampingX: float = 0.0
    dampingY: float = 0.0
    dampingZ: float = 0.0
    dampingXX: float = 0.0
    dampingYY: float = 0.0
    dampingZZ: float = 0.0


class PropertyMass(Property, speckle_type=STRUCTURAL_PROPERTY + ".PropertyMass"):
    mass: float = 0.0
    inertiaXX: float = 0.0
    inertiaYY: float = 0.0
    inertiaZZ: float = 0.0
    inertiaXY: float = 0.0
    inertiaYZ: float = 0.0
    inertiaZX: float = 0.0
    massModified: Optional[bool] = None
    massModifierX: float = 0.0
    massModifierY: float = 0.0
    massModifierZ: float = 0.0


class PropertySpring(Property, speckle_type=STRUCTURAL_PROPERTY + ".PropertySpring"):
    springType: Optional[PropertyTypeSpring] = None
    springCurveX: float = 0.0
    stiffnessX: float = 0.0
    springCurveY: float = 0.0
    stiffnessY: float = 0.0
    springCurveZ: float = 0.0
    stiffnessZ: float = 0.0
    springCurveXX: float = 0.0
    stiffnessXX: float = 0.0
    springCurveYY: float = 0.0
    stiffnessYY: float = 0.0
    springCurveZZ: float = 0.0
    stiffnessZZ: float = 0.0
    dampingRatio: float = 0.0
    dampingX: float = 0.0
    dampingY: float = 0.0
    dampingZ: float = 0.0
    dampingXX: float = 0.0
    dampingYY: float = 0.0
    dampingZZ: float = 0.0
    matrix: float = 0.0
    postiveLockup: float = 0.0
    frictionCoefficient: float = 0.0


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
