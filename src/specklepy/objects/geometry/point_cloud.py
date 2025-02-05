from dataclasses import dataclass
from typing import List

from specklepy.objects.base import Base
from specklepy.objects.geometry.point import Point
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class PointCloud(Base, IHasUnits, speckle_type="Objects.Geometry.PointCloud"):
    """
    a collection of 3-dimensional points
    """

    points: List[Point]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"points: {len(self.points)}, "
            f"units: {self.units})"
        )

    # sizes and colors could be added in the future
