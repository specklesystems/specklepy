from typing import Optional

from specklepy.objects.base import Base


class ColorProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.ColorProxy",
):
    """
    Represents a color that is found on objects and collections in a root collection.
    """

    objects: list[str]
    value: int
    name: str | None  # nullable but required


class GroupProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.GroupProxy",
):
    """
    Grouped objects with a meaningful way for host application so use this proxy if you want to group object references for any purpose.
    i.e. in rhino -> creating group make objects selectable/moveable/editable together.
    """

    objects: list[str]
    name: str
