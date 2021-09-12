from enum import Enum
from typing import Any, List, Type, Union

from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base


class CurveTypeEncoding(int, Enum):
    Arc = 0
    Circle = 1
    Curve = 2
    Ellipse = 3
    Line = 4
    Polyline = 5
    Polycurve = 6

    @property
    def object_class(self) -> Type:
        from . import geometry
        if self == self.Arc:
            return geometry.Arc
        elif self == self.Circle:
            return geometry.Circle
        elif self == self.Curve:
            return geometry.Curve
        elif self == self.Ellipse:
            return geometry.Ellipse
        elif self == self.Line:
            return geometry.Line
        elif self == self.Polyline:
            return geometry.Polyline
        elif self == self.Polycurve:
            return geometry.Polycurve
        raise SpeckleException(
            f'No corresponding object class for CurveTypeEncoding: {self}')


def curve_from_list(args: List[float]):
    curve_type = CurveTypeEncoding(args[0])
    return curve_type.object_class.from_list(args)


class CurveArray:

    def __init__(self, array: List[float]):
        self.array = array

    @classmethod
    def from_curve(cls, curve: Base) -> 'CurveArray':
        return cls(array=curve.to_list())

    @classmethod
    def from_curves(cls, curves: List[Base]) -> 'CurveArray':
        array = []
        for curve in curves:
            curve_list = curve.to_list()
            curve_list.insert(0, len(curve_list))
            array.extend(curve_list)
        return cls(array=array)

    @staticmethod
    def curve_from_list(args: List[float]) -> Base:
        curve_type = CurveTypeEncoding(args[0])
        return curve_type.object_class.from_list(args)

    @property
    def type(self) -> CurveTypeEncoding:
        return CurveTypeEncoding(self.array[0])

    def to_curve(self) -> Base:
        return self.type.object_class.from_list(self.array)

    def to_curves(self) -> List[Base]:
        index = 0
        curves = []
        while index < len(self.array):
            chunk_length = self.array[index]
            chunk_start = int(index + 1)
            chunk_end = int(chunk_start + chunk_length)
            chunk_data = self.array[chunk_start:chunk_end]
            child_array = self.__class__(array=chunk_data)
            curves.append(child_array.to_curve())
            index = chunk_end
        return curves
