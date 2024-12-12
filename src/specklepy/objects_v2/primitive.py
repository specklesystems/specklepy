from typing import Any, List

from specklepy.objects.base import Base

NAMESPACE = "Objects.Primitive"


class Interval(Base, speckle_type=f"{NAMESPACE}.Interval"):
    start: float = 0.0
    end: float = 0.0

    def length(self):
        return abs(self.start - self.end)

    @classmethod
    def from_list(cls, args: List[Any]) -> "Interval":
        return cls(start=args[0], end=args[1])

    def to_list(self) -> List[Any]:
        return [self.start, self.end]


class Interval2d(Base, speckle_type=f"{NAMESPACE}.Interval2d"):
    u: Interval
    v: Interval
