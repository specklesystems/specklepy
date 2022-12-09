from typing import Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry import Plane


class Axis(Base, speckle_type="Objects.Structural.Geometry.Axis"):
    name: Optional[str] = None
    axisType: Optional[str] = None
    plane: Optional[Plane] = None
