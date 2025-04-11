from dataclasses import dataclass
from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry.box import Box
from specklepy.objects.geometry.polyline import Polyline
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Curve(
    Base,
    ICurve,
    IHasArea,
    IHasUnits,
    speckle_type="Objects.Geometry.Curve",
    detachable={"points", "weights", "knots", "displayValue"},
    chunkable={"points": 31250, "weights": 31250, "knots": 31250},
):
    """
    a NURBS curve
    """

    degree: int
    periodic: bool
    rational: bool
    points: List[float]
    weights: List[float]
    knots: List[float]
    closed: bool
    displayValue: Polyline
    bbox: Optional[Box] = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"degree: {self.degree}, "
            f"periodic: {self.periodic}, "
            f"rational: {self.rational}, "
            f"closed: {self.closed}, "
            f"units: {self.units})"
        )

    @property
    def length(self) -> float:
        return self.__dict__.get("_length", 0.0)

    @length.setter
    def length(self, value: float) -> None:
        self.__dict__["_length"] = value

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value
