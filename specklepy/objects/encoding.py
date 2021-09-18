from enum import Enum
from typing import Any, Callable, List, Type

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


class ObjectArray:

    def __init__(self) -> None:
        self.data = []

    @classmethod
    def from_objects(cls, objects: List[Base]) -> 'ObjectArray':
        data_chunk = cls()
        if len(objects) == 0:
            return data_chunk

        speckle_type = objects[0].speckle_type

        for obj in objects:
            if speckle_type != obj.speckle_type:
                raise SpeckleException(
                    'All objects in chunk should have the same speckle_type. '
                    f'Found {speckle_type} and {obj.speckle_type}'
                )
            data_chunk.encode_object(object=obj)

        return data_chunk

    @staticmethod
    def decode_data(data: List[Any], decoder: Callable[[List[Any]], Base]) -> List[Base]:
        index = 0
        unchunked_data = []
        while index < len(data):
            chunk_length = data[index]
            chunk_start = int(index + 1)
            chunk_end = int(chunk_start + chunk_length)
            chunk_data = data[chunk_start:chunk_end]
            decoded_data = decoder(chunk_data)
            unchunked_data.append(decoded_data)
            index = chunk_end
        return unchunked_data

    def decode(self, decoder: Callable[[List[Any]], Any]):
        return self.decode_data(data=self.data, decoder=decoder)

    def encode_object(self, object: Base):
        chunk = object.to_list()
        chunk.insert(0, len(chunk))
        self.data.extend(chunk)


class CurveArray(ObjectArray):

    @classmethod
    def from_curve(cls, curve: Base) -> 'CurveArray':
        crv_array = cls()
        crv_array.data = curve.to_list()
        return crv_array

    @classmethod
    def from_curves(cls, curves: List[Base]) -> 'CurveArray':
        data = []
        for curve in curves:
            curve_list = curve.to_list()
            curve_list.insert(0, len(curve_list))
            data.extend(curve_list)
        crv_array = cls()
        crv_array.data = data
        return crv_array

    @staticmethod
    def curve_from_list(args: List[float]) -> Base:
        curve_type = CurveTypeEncoding(args[0])
        return curve_type.object_class.from_list(args)

    @property
    def type(self) -> CurveTypeEncoding:
        return CurveTypeEncoding(self.data[0])

    def to_curve(self) -> Base:
        return self.type.object_class.from_list(self.data)

    @classmethod
    def _curve_decoder(cls, data: List[float]) -> Base:
        crv_array = cls()
        crv_array.data = data
        return crv_array.to_curve()

    def to_curves(self) -> List[Base]:
        return self.decode(decoder=self._curve_decoder)
