from ifcopenshell import file
from ifcopenshell.entity_instance import entity_instance

from specklepy.objects.proxies import ConnectionProxy


class ConnectionProxyManager:
    """
    Builds ConnectionProxies from IFC port connectivity.

    Distribution elements (pipes, fittings, terminals) carry
    ``IfcDistributionPort`` nodes, and ``IfcRelConnectsPorts`` links a pair of
    ports. Resolving each port back to its owning element (via the nesting
    relationship, or the legacy port-to-element relationship) yields the
    element-level network graph: one ConnectionProxy per edge.
    """

    def __init__(self):
        self._connection_proxies: list[ConnectionProxy] = []

    @property
    def connection_proxies(self) -> list[ConnectionProxy]:
        return self._connection_proxies

    @staticmethod
    def _owner_of_port(port: entity_instance | None) -> entity_instance | None:
        if port is None:
            return None
        # IFC4: port nested under its element via IfcRelNests (inverse: Nests)
        for rel in getattr(port, "Nests", None) or []:
            if rel.RelatingObject is not None:
                return rel.RelatingObject
        # Legacy: IfcRelConnectsPortToElement (inverse: ContainedIn)
        for rel in getattr(port, "ContainedIn", None) or []:
            if getattr(rel, "RelatedElement", None) is not None:
                return rel.RelatedElement
        return None

    def extract(self, ifc_file: file) -> None:
        for rel in ifc_file.by_type("IfcRelConnectsPorts"):
            source = self._owner_of_port(rel.RelatingPort)
            target = self._owner_of_port(rel.RelatedPort)
            if source is None or target is None:
                continue

            source_id = getattr(source, "GlobalId", None)
            target_id = getattr(target, "GlobalId", None)
            if not source_id or not target_id:
                continue

            self._connection_proxies.append(
                ConnectionProxy(
                    sourceAppId=source_id,
                    targetAppId=target_id,
                    applicationId=getattr(rel, "GlobalId", None),
                    sourceFlowDirection=getattr(
                        rel.RelatingPort, "FlowDirection", None
                    ),
                    targetFlowDirection=getattr(
                        rel.RelatedPort, "FlowDirection", None
                    ),
                )
            )
