from abc import ABCMeta
from dataclasses import dataclass

from devtools import debug

from specklepy.api.operations import deserialize, serialize
from specklepy.objects.base import Base

b = Base("asdf", 10, None)


@dataclass(kw_only=True)
class IRhino(Base, speckle_type="IRhino", metaclass=ABCMeta):
    rhino_name: str


@dataclass(kw_only=True)
class IRevit(Base, speckle_type="IRevit", metaclass=ABCMeta):
    revit_name: str


@dataclass(kw_only=True)
class Point(Base, speckle_type="Objects.Geometry.Point_V3"):
    x: float
    y: float
    z: float = 0.0


@dataclass(kw_only=True)
class RhinoPoint(Point, IRhino, speckle_type="Objects.Geometry.RhinoPoint"):
    pass


t = RhinoPoint(x=1, y=2, rhino_name="asdf")


ser_t = serialize(t)


t_again = deserialize(ser_t)

debug(ser_t)
debug(t_again)
