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
    objects: List[str] = field(default_factory=list)
    value: int
    name: Optional[str] = None


@dataclass(kw_only=True)
class GroupProxy(
    Base,
    speckle_type="Models.Proxies.GroupProxy",
    detachable={"objects"},
):

    objects: List[str] = field(default_factory=list)
    name: str = field(default="Unnamed Group")


@dataclass(kw_only=True)
class InstanceProxy(
    Base,
    IHasUnits,
    speckle_type="Models.Proxies.InstanceProxy",
):

    definition_id: str
    transform: List[float] = field(default_factory=list)
    max_depth: int = 50


@dataclass(kw_only=True)
class InstanceDefinitionProxy(
    Base,
    speckle_type="Models.Proxies.InstanceDefinitionProxy",
    detachable={"objects"},
):

    objects: List[str] = field(default_factory=list)
    max_depth: int = 50
    name: str = field(default="Unnamed Instance")
