from dataclasses import dataclass
from typing import List

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits, ITransformable
from specklepy.objects.models.units import Units


@dataclass(kw_only=True)
class Vector(Base, IHasUnits, ITransformable, speckle_type="Objects.Geometry.Vector"):
    """
    a 3-dimensional vector
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, units: {self.units})"

    @property
    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_list(cls, coords: List[float], units: str | Units) -> "Vector":
        return cls(x=coords[0], y=coords[1], z=coords[2], units=units)

    def transform_to(self, transform):
        m = transform.matrix
        tx = self.x * m[0] + self.y * m[1] + self.z * m[2]
        ty = self.x * m[4] + self.y * m[5] + self.z * m[6]
        tz = self.x * m[8] + self.y * m[9] + self.z * m[10]
        transformed = Vector(x=tx, y=ty, z=tz, units=self.units,
                             applicationId=self.applicationId)
        return True, transformed
