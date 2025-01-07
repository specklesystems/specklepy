from dataclasses import dataclass, field
from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class ColorProxy(
    Base,
    speckle_type="Models.Proxies.ColorProxy",
    detachable={"objects"},
):
    objects: List[str]
    value: int
    name: Optional[str]


@dataclass(kw_only=True)
class GroupProxy(
    Base,
    speckle_type="Models.Proxies.GroupProxy",
    detachable={"objects"},
):

    objects: List[str]
    name: str


@dataclass(kw_only=True)
class InstanceProxy(
    Base,
    IHasUnits,
    speckle_type="Models.Proxies.InstanceProxy",
):

    definition_id: str
    transform: List[float]
    max_depth: int


@dataclass(kw_only=True)
class InstanceDefinitionProxy(
    Base,
    speckle_type="Models.Proxies.InstanceDefinitionProxy",
    detachable={"objects"},
):

    objects: List[str]
    max_depth: int
    name: str
