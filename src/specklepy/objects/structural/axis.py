from enum import Enum
from typing import Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry import Plane


class AxisType(int, Enum):
    Cartesian = 0
    Cylindrical = 1
    Spherical = 2


class Axis(Base, speckle_type="Objects.Structural.Geometry.Axis"):
    name: Optional[str] = None
    axisType: Optional[AxisType] = None
    plane: Optional[Plane] = None
