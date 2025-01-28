import math
from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.primitive import Interval
from specklepy.objects.interfaces import IHasUnits, IHasVolume, IHasArea


@dataclass(kw_only=True)
class Box(Base, IHasUnits, IHasArea, IHasVolume, speckle_type="Objects.Geometry.Box"):
    """
    a 3-dimensional box oriented on a plane
    """
    basePlane: Plane
    xSize: Interval
    ySize: Interval
    zSize: Interval

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(basePlane: {self.basePlane}, xSize: {self.xSize}, ySize: {self.ySize}, zSize: {self.zSize}, units: {self.units})"

    @property
    def area(self) -> float:
        return 2 * (self.xSize.length * self.ySize.length + self.xSize.length * self.zSize.length + self.ySize.length * self.zSize.length)

    @property
    def volume(self) -> float:
        return self.xSize.length * self.ySize.length * self.zSize.length
