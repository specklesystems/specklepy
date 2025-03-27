from dataclasses import dataclass, field
from typing import List

from specklepy.objects.base import Base


@dataclass(kw_only=True)
class Collection(
    Base,
    # TODO: add deprecated speckle_types
    speckle_type="Speckle.Core.Models.Collections.Collection",
    detachable={"elements"},
):
    """
    A simple container for organising objects within a model
    and preserving object hierarchy.

    A container is defined by a human-readable name a unique applicationId and
    its list of contained elements.
    The elements can include an unrestricted number of Base objects including
    additional nested Collections.

    Note:
        A Collection can be for example a Layer in Rhino/AutoCad,
        a collection in Blender, or a Category in Revit.
        The location of each collection in the hierarchy of collections in a commit
        will be retrieved through commit traversal.

    Attributes:
        name: The human-readable name of the Collection. This name is not necessarily
        unique within a commit. Set the applicationId for a unique identifier.
        elements: The elements contained in this Collection.
        This may include additional nested Collections
    """

    name: str
    elements: List[Base] = field(default_factory=list)
