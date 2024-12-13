from dataclasses import dataclass, field
from typing import List
from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits


@dataclass(kw_only=True)
class InstanceProxy(
    Base,
    IHasUnits,
    speckle_type="Models.Instances.InstanceProxy",
):

    definition_id: str
    transform: List[float] = field(default_factory=list)
    max_depth: int = 50


@dataclass(kw_only=True)
class InstanceDefinitionProxy(
    Base,
    speckle_type="Models.Instances.InstanceDefinitionProxy",
    detachable={"objects"},
):

    objects: List[str] = field(default_factory=list)
    max_depth: int = 50
    name: str = field(default="Unnamed Instance")
