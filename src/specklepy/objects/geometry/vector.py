from dataclasses import dataclass
from typing import List, Any

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits, ITransformable
from specklepy.objects.models.units import (
    Units,
    get_encoding_from_units
)


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

    def to_list(self) -> List[Any]:
        """
        returns a serializable list of format:
        [total_length, speckle_type, units_encoding, x, y, z]
        """
        result = [self.x, self.y, self.z]
        result.insert(0, get_encoding_from_units(self.units))
        result.insert(0, self.speckle_type)
        result.insert(0, len(result) + 1)  # +1 for the length we're adding
        return result

    @classmethod
    def from_list(cls, coords: List[Any], units: str | Units) -> "Vector":
        """
        creates a Vector from a list of format:
        [total_length, speckle_type, units_encoding, x, y, z]
        """
        x, y, z = coords[3:6]  # geometric data starts at index 3
        return cls(x=x, y=y, z=z, units=units)

    def transform_to(self, transform):
        m = transform.matrix
        tx = self.x * m[0] + self.y * m[1] + self.z * m[2]
        ty = self.x * m[4] + self.y * m[5] + self.z * m[6]
        tz = self.x * m[8] + self.y * m[9] + self.z * m[10]
        transformed = Vector(x=tx, y=ty, z=tz, units=self.units,
                             applicationId=self.applicationId)
        return True, transformed
