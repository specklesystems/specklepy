from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from specklepy.objects.base import Base
from specklepy.objects.geometry import Plane, Point
from specklepy.objects.interfaces import IHasUnits


class AlignmentHorizontal(Enum):
    Left = 0
    Center = 1
    Right = 2


class AlignmentVertical(Enum):
    Top = 0
    Center = 1
    Bottom = 2


@dataclass(kw_only=True)
class Text(Base, IHasUnits, speckle_type="Objects.Annotation.Text"):
    """
    Text class for representation in the viewer.
    Units will be 'Units.None' if the text size is defined in pixels.
    """

    value: str  # Plain text, without formatting
    origin: Point  # Relation to the text is defined by AlignmentH and AlignmentV
    height: float  # Font height in linear units or pixels (if Units.None)
    alignmentH: AlignmentHorizontal = field(
        default_factory=lambda: AlignmentHorizontal.Left
    )
    alignmentV: AlignmentVertical = field(default_factory=lambda: AlignmentVertical.Top)
    plane: Optional[Plane] = field(
        default_factory=lambda: None
    )  # None if the text object orientation follows camera view
    maxWidth: Optional[float] = field(
        default_factory=lambda: None
    )  # Maximum width of the text field. None, if don't split into lines

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"value: {self.value}, "
            f"origin: {self.origin}, "
            f"height: {self.height}, "
            f"alignmentH: {self.alignmentH}, "
            f"alignmentV: {self.alignmentV}, "
            f"plane: {self.plane}, "
            f"maxWidth: {self.maxWidth}, "
            f"units: {self.units})"
        )
