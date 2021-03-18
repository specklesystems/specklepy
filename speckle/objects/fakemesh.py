from speckle.objects.geometry import Point
from typing import List, Optional

from .base import Base

CHUNKABLE_PROPS = {
    "vertices": 100,
    "faces": 100,
    "colors": 100,
    "textureCoordinates": 100,
    "test_bases": 10,
}

DETACHABLE = {"detach_this", "origin", "detached_list"}


class FakeMesh(Base):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    test_bases: List[Base] = None
    detach_this: Base = None
    detached_list: List[Base] = None
    _origin: Point = None

    def __init__(self, **kwargs) -> None:
        super(FakeMesh, self).__init__(**kwargs)
        self._chunkable = dict(self._chunkable, **CHUNKABLE_PROPS)
        self._detachable = self._detachable.union(DETACHABLE)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value: Point):
        self._origin = value
