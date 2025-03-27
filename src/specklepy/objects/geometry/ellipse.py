from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.interfaces import ICurve, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Ellipse(
    Base, IHasUnits, ICurve, IHasArea, speckle_type="Objects.Geometry.Ellipse"
):
    """
    an ellipse
    """

    plane: Plane
    first_radius: float
    second_radius: float

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
