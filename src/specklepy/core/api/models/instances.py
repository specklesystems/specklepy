from specklepy.objects.base import Base


class InstanceProxy(
    Base,
    speckle_type="Speckle.Core.Models.Instances.InstanceProxy",
):
    """
    A proxy class for an instance (e.g, a rhino block, or an autocad block reference).
    """

    definitionId: str
    transform: list[float]
    units: str
    maxDepth: int


class InstanceDefinitionProxy(
    Base,
    speckle_type="Speckle.Core.Models.Instances.InstanceDefinitionProxy",
):
    """
    A proxy class for an instance definition.
    """

    objects: list[str]
    maxDepth: int
    name: str
