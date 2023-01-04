from enum import Enum
from typing import List, Optional

from specklepy.objects.geometry import Point

from .base import Base

CHUNKABLE_PROPS = {
    "vertices": 100,
    "faces": 100,
    "colors": 100,
    "textureCoordinates": 100,
    "test_bases": 10,
}

DETACHABLE = {"detach_this", "origin", "detached_list"}


class FakeGeo(Base, chunkable={"dots": 50}, detachable={"pointslist"}):
    pointslist: Optional[List[Base]] = None
    dots: Optional[List[int]] = None


class FakeDirection(Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


class FakeMesh(FakeGeo, chunkable=CHUNKABLE_PROPS, detachable=DETACHABLE):
    vertices: Optional[List[float]] = None
    faces: Optional[List[int]] = None
    colors: Optional[List[int]] = None
    textureCoordinates: Optional[List[float]] = None
    cardinal_dir: Optional[FakeDirection] = None
    test_bases: Optional[List[Base]] = None
    detach_this: Optional[Base] = None
    detached_list: Optional[List[Base]] = None
    _origin: Optional[Point] = None

    # def __init__(self, **kwargs) -> None:
    #     super(FakeMesh, self).__init__(**kwargs)
    #     self.add_chunkable_attrs(**CHUNKABLE_PROPS)
    #     self.add_detachable_attrs(DETACHABLE)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value: Point):
        self._origin = value
