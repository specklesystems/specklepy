from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel
from .base import Base

CHUNKABLE_PROPS = {
    "vertices": 2000,
    "faces": 2000,
    "colors": 2000,
    "textureCoordinates": 2000,
}


class Mesh(Base):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    id: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    applicationId: Optional[str] = None
    speckle_type: Optional[str] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chunkable.update(CHUNKABLE_PROPS)
