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
class SystemProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.SystemProxy",
):
    """
    Stores logical system (e.g. MEP distribution system) membership in root
    collections. Sourced from IFC ``IfcSystem`` / ``IfcDistributionSystem``
    grouping (``IfcRelAssignsToGroup``).

    Args:
        objects (list): application ids of the member elements
        name (str): the system name (e.g. "S_Schmutzwasser")
        applicationId (str): the IfcSystem GlobalId
        systemType (str | None): predefined/object type, when present
    """

    objects: List[str]
    name: str
    applicationId: Optional[str]
    systemType: Optional[str] = None


@dataclass(kw_only=True)
class ConnectionProxy(
    Base,
    speckle_type="Speckle.Core.Models.Proxies.ConnectionProxy",
):
    """
    Stores a single network-connectivity edge between two elements, sourced
    from IFC port connectivity (``IfcRelConnectsPorts`` resolved through the
    ports' owning elements via ``IfcRelNests`` / ``IfcRelConnectsPortToElement``).

    An edge is a directed pair with distinct endpoint roles, so the endpoints
    are named fields rather than a positional ``objects`` list.

    Args:
        sourceAppId (str): application id of the source-end element
            (owner of the relating port)
        targetAppId (str): application id of the target-end element
            (owner of the related port)
        applicationId (str): the IfcRelConnectsPorts GlobalId
        sourceFlowDirection (str | None): the source-end (relating) port's
            FlowDirection (SOURCE / SINK / SOURCEANDSINK / NOTDEFINED)
        targetFlowDirection (str | None): the target-end (related) port's
            FlowDirection. Capturing both ends lets a consumer orient the edge
            (SOURCE→SINK) where the data defines it; gravity systems remain
            SOURCEANDSINK on both ends and stay undirected.
    """

    sourceAppId: str
    targetAppId: str
    applicationId: Optional[str]
    sourceFlowDirection: Optional[str] = None
    targetFlowDirection: Optional[str] = None


@dataclass(kw_only=True)
class InstanceProxy(
    Base,
    IHasUnits,
    speckle_type="Speckle.Core.Models.Instances.InstanceProxy",
):
    definitionId: str
    transform: List[float]
    maxDepth: int


@dataclass(kw_only=True)
class InstanceDefinitionProxy(
    Base,
    speckle_type="Speckle.Core.Models.Instances.InstanceDefinitionProxy",
    detachable={"objects"},
):
    objects: List[str]
    maxDepth: int
    name: str


@dataclass(kw_only=True)
class LevelProxy(
    Base,
    speckle_type="Objects.Other.LevelProxy",
    detachable={"objects"},
):
    """
    used to store building storey to object relationships in root collections

    Args:
        objects (list): the list of application ids of objects in this building storey
        value (DataObject): the building storey data object with all properties
        applicationId (str): the GUID of the building storey
    """

    objects: List[str]
    value: Base
    applicationId: str


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
