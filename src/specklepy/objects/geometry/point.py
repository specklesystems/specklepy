from dataclasses import dataclass
from typing import List, Tuple, Any

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits, ITransformable
from specklepy.objects.models.units import (
    Units,
    get_scale_factor,
    get_units_from_string,
    get_encoding_from_units
)


@dataclass(kw_only=True)
class Point(Base, IHasUnits, ITransformable, speckle_type="Objects.Geometry.Point"):
    """
    a 3-dimensional point
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, units: {self.units})"

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
    def from_list(cls, coords: List[Any], units: str | Units) -> "Point":
        """
        creates a Point from a list of format:
        [total_length, speckle_type, units_encoding, x, y, z]
        """
        x, y, z = coords[3:6]  # geometric data starts at index 3
        return cls(x=x, y=y, z=z, units=units)

    @classmethod
    def from_coords(cls, x: float, y: float, z: float, units: str | Units) -> "Point":
        return cls(x=x, y=y, z=z, units=units)

    def transform_to(self, transform) -> Tuple[bool, "Point"]:
        """
        transform this point using the given transform
        """
        m = transform.matrix
        tx = self.x * m[0] + self.y * m[1] + self.z * m[2] + m[3]
        ty = self.x * m[4] + self.y * m[5] + self.z * m[6] + m[7]
        tz = self.x * m[8] + self.y * m[9] + self.z * m[10] + m[11]

        transformed = Point(
            x=tx,
            y=ty,
            z=tz,
            units=self.units,
            applicationId=self.applicationId
        )
        return True, transformed

    def distance_to(self, other: "Point") -> float:
        """
        calculates the distance between this point and another given point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"Expected Point object, got {type(other)}")

        # if units are the same perform direct calculation
        if self.units == other.units:
            dx = other.x - self.x
            dy = other.y - self.y
            dz = other.z - self.z
            return (dx * dx + dy * dy + dz * dz) ** 0.5

        # convert other point's coordinates to this point's units
        scale_factor = get_scale_factor(
            get_units_from_string(
                other.units), get_units_from_string(self.units)
        )

        dx = (other.x * scale_factor) - self.x
        dy = (other.y * scale_factor) - self.y
        dz = (other.z * scale_factor) - self.z

        return (dx * dx + dy * dy + dz * dz) ** 0.5
