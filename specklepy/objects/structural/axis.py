from ..base import Base
from ..geometry import Plane


class Axis(Base, speckle_type="Objects.Structural.Geometry.Axis"):
    name: str = None
    axisType: str = None
    plane: Plane = None