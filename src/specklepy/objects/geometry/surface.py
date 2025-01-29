from dataclasses import dataclass
from typing import List

from specklepy.objects.base import Base
from specklepy.objects.geometry.control_point import ControlPoint
from specklepy.objects.interfaces import IHasArea, IHasUnits
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Surface(Base, IHasArea, IHasUnits, speckle_type="Objects.Geometry.Surface"):
    """
    a surface in nurbs form
    """

    degreeU: int
    degreeV: int
    rational: bool
    pointData: List[float]
    countU: int
    countV: int
    knotsU: List[float]
    knotsV: List[float]
    domainU: Interval
    domainV: Interval
    closedU: bool
    closedV: bool

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value

    def get_control_points(self) -> List:
        """
        gets the control points of this surface
        """

        matrix = [[] for _ in range(self.countU)]

        for i in range(0, len(self.pointData), 4):
            u_index = i // (self.countV * 4)
            x, y, z, w = self.pointData[i : i + 4]
            matrix[u_index].append(
                ControlPoint(x=x, y=y, z=z, weight=w, units=self.units)
            )

        return matrix

    def set_control_points(self, value: List) -> None:
        """
        sets the control points of this surface
        """
        data = []
        self.countU = len(value)
        self.countV = len(value[0])

        for row in value:
            for pt in row:
                data.extend([pt.x, pt.y, pt.z, pt.weight])

        self.pointData = data
