from abc import ABCMeta
from dataclasses import dataclass
from typing import List

from devtools import debug

from specklepy.api.operations import deserialize, serialize
from specklepy.objects.base import Base

b = Base("asdf", 10, None)


@dataclass
class IBase(Base, speckle_type="IBase", metaclass=ABCMeta):
    pass


@dataclass(kw_only=True)
class IRhino(IBase, speckle_type="IRhino", metaclass=ABCMeta):
    rhino_name: str


@dataclass(kw_only=True)
class IRevit(Base, speckle_type="IRevit", metaclass=ABCMeta):
    revit_name: str


@dataclass(kw_only=True)
class Point(Base, speckle_type="Objects.Geometry.Point_V3"):
    p: List[float]


@dataclass(kw_only=True)
class RhinoPoint(Point, IRhino, speckle_type="Objects.Geometry.RhinoPoint"):
    pass


t = RhinoPoint(p=[1, 2, 3], rhino_name="asdf")


ser_t = serialize(t)


t_again = deserialize(ser_t)

debug(ser_t)
