from dataclasses import dataclass
from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits
from specklepy.objects.other import RenderMaterial


@dataclass(kw_only=True)
class ColorProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.ColorProxy",
    detachable={"objects"},
):
    objects: List[str]
    value: int
    name: Optional[str]


@dataclass(kw_only=True)
class GroupProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.GroupProxy",
    detachable={"objects"},
):
    objects: List[str]
    name: str


@dataclass(kw_only=True)
class InstanceProxy(
    Base,
    IHasUnits,
    speckle_type="Speckle.Core.Models.Instances.InstanceProxy",
):
    definition_id: str
    transform: List[float]
    max_depth: int


@dataclass(kw_only=True)
class InstanceDefinitionProxy(
    Base,
    speckle_type="Speckle.Core.Models.Instances.InstanceDefinitionProxy",
    detachable={"objects"},
):
    objects: List[str]
    max_depth: int
    name: str


@dataclass(kw_only=True)
class RenderMaterialProxy(
    Base,
    speckle_type="Objects.Other.RenderMaterialProxy",
    detachable={"objects"},
):
    """
    used to store render material to object relationships in root collections

    Args:
        objects (list): the list of application ids of objects used by render material
        value (RenderMaterial): the render material used by the objects
    """

    objects: List[str]
    value: RenderMaterial
