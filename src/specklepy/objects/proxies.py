from dataclasses import dataclass, field
from typing import List, Optional
from specklepy.objects.base import Base


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
