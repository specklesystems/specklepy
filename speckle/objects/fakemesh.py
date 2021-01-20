from typing import List, Optional

from .base import Base

CHUNKABLE_PROPS = {
    "vertices": 100,
    "faces": 100,
    "colors": 100,
    "textureCoordinates": 100,
    "test_bases": 10,
}


class FakeMesh(Base):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    test_bases: List[Base] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chunkable.update(CHUNKABLE_PROPS)
