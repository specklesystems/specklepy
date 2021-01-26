from typing import List
from pydantic import BaseModel
from speckle.objects.base import Base


class Point(Base):
    value: List[float] = [0, 0, 0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value: {self.value}, id: {self.id}, speckle_type: {self.speckle_type})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def x(self):
        return self.value[0]

    @property
    def y(self):
        return self.value[1]

    @property
    def z(self):
        return self.value[2]
