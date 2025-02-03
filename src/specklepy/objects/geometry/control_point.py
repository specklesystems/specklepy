from dataclasses import dataclass

from specklepy.objects.geometry.point import Point


@dataclass(kw_only=True)
class ControlPoint(Point, speckle_type="Objects.Geometry.ControlPoint"):
    """
    a single 3-dimensional point with weight
    """

    weight: float

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"x: {self.x}, "
            f"y: {self.y}, "
            f"z: {self.z}, "
            f"weight: {self.weight}, "
            f"units: {self.units})"
        )
