from ifcopenshell import file
from ifcopenshell.entity_instance import entity_instance

from specklepy.objects.proxies import SystemProxy


class SystemProxyManager:
    """
    Builds SystemProxies from IFC system grouping.

    IFC groups distribution-network elements into ``IfcSystem`` /
    ``IfcDistributionSystem`` via ``IfcRelAssignsToGroup``. Each such group
    becomes one SystemProxy listing its member application ids, so the EAV
    ingestion can denormalise system membership onto each element.
    """

    def __init__(self):
        self._system_proxies: dict[str, SystemProxy] = {}

    @property
    def system_proxies(self) -> dict[str, SystemProxy]:
        return self._system_proxies

    def extract(self, ifc_file: file) -> None:
        for rel in ifc_file.by_type("IfcRelAssignsToGroup"):
            group: entity_instance | None = rel.RelatingGroup
            if group is None:
                continue
            if not (group.is_a("IfcSystem") or group.is_a("IfcDistributionSystem")):
                continue

            group_id = getattr(group, "GlobalId", None)
            if not group_id:
                continue

            members = [
                o.GlobalId
                for o in (rel.RelatedObjects or [])
                if getattr(o, "GlobalId", None)
            ]
            if not members:
                continue

            existing = self._system_proxies.get(group_id)
            if existing is not None:
                # Same system can be assigned in multiple relationships
                existing.objects.extend(members)
                continue

            system_type = getattr(group, "PredefinedType", None) or getattr(
                group, "ObjectType", None
            )
            self._system_proxies[group_id] = SystemProxy(
                objects=members,
                name=group.Name or group_id,
                applicationId=group_id,
                systemType=system_type,
            )
