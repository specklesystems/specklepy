from dataclasses import dataclass
from specklepy.objects_v3.models.base import Base


@dataclass(kw_only=True)
class Interval(Base, speckle_type="Objects.Primitive.Interval"):
    start: float
    end: float

    @property
    def length(self) -> float:
        return abs(self.end - self.start)

    def __str__(self) -> str:
        return f"{super().__str__()}[{self.start}, {self.end}]"

    @classmethod
    def unit_interval(cls) -> 'Interval':
        return cls(0, 1)
