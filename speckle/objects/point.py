from typing import List
from speckle.objects.base import Base


class Point(Base):
    value: List[int or float] = [0, 0, 0]

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

    @x.setter
    def x(self, value: int or float):
        if isinstance(value, (int, float)):
            self.value[0] = value

    @y.setter
    def y(self, value: int or float):
        if isinstance(value, (int, float)):
            self.value[1] = value

    @z.setter
    def z(self, value: int or float):
        if isinstance(value, (int, float)):
            self.value[2] = value
