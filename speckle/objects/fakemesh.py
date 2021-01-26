from speckle.objects.point import Point
from typing import List, Optional

from .base import Base

CHUNKABLE_PROPS = {
    "vertices": 100,
    "faces": 100,
    "colors": 100,
    "textureCoordinates": 100,
    "test_bases": 10,
}

DETACHABLE = ["detach_this", "origin"]


class FakeMesh(Base):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    test_bases: List[Base] = None
    detach_this: Base = None
    _origin: Point = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chunkable.update(CHUNKABLE_PROPS)
        self._detachable.extend(DETACHABLE)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value: Point):
        self._origin = value