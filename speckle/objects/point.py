from typing import Any
from speckle.objects.base import Base


class Point(Base, speckle_type="Objects.Geometry.Point"):
    x: float = 0
    y: float = 0
    z: float = 0

    def __init__(self, x: float = 0, y: float = 0, z: float = 0, **data: Any) -> None:
        super().__init__(**data)
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, id: {self.id}, speckle_type: {self.speckle_type})"

    def __str__(self) -> str:
        return self.__repr__()
