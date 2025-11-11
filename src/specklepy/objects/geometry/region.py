from dataclasses import dataclass, field
from typing import List

from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.objects.geometry.box import Box
from specklepy.objects.geometry.mesh import Mesh
from specklepy.objects.interfaces import ICurve, IDisplayValue, IHasArea, IHasUnits


@dataclass(kw_only=True)
class Region(
    Base,
    IHasArea,
    IDisplayValue[List[Mesh]],
    IHasUnits,
    speckle_type="Objects.Geometry.Region",
    detachable={"displayValue"},
):
    """
    Flat shape, defined by an outer boundary and inner loops.
    """

    boundary: ICurve
    innerLoops: List[ICurve]
    hasHatchPattern: bool
    bbox: Box | None = None
    # unlike C#, constructor will require displayValue, even if it's empty
    displayValue: List[Mesh]
    _displayValue: List[Mesh] = field(repr=False, init=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"units: {self.units}, "
            f"has_hatch_pattern: {self.hasHatchPattern}, "
            f"inner_loops: {len(self.innerLoops)})"
        )

    @property
    def area(self) -> float:
        return self.__dict__.get("_area", 0.0)

    @area.setter
    def area(self, value: float) -> None:
        self.__dict__["_area"] = value

    @property
    def displayValue(self) -> List[Mesh]:
        return self._displayValue

    @displayValue.setter
    def displayValue(self, value: list):
        if isinstance(value, list):
            self._displayValue = value
        else:
            raise SpeckleException(
                f"'displayValue' value should be List, received {type(value)}"
            )
