from typing import Sequence

from specklepy.objects.base import Base
from specklepy.objects.proxies import InstanceDefinitionProxy


class InstanceProxyManager:
    def __init__(self):
        self._instance_definition_proxies: dict[str, InstanceDefinitionProxy] = {}
        """definition proxies to be added directly to the root"""
        self._instance_geometry: dict[str, Base] = {}
        """The geometry that will be added in it's own collection under the root"""

    @property
    def instance_definition_proxies(self) -> dict[str, InstanceDefinitionProxy]:
        return self._instance_definition_proxies

    @property
    def instance_geometry(self) -> dict[str, Base]:
        return self._instance_geometry

    def add_display_value_definitions(self, geometry: Sequence[Base]) -> list[str]:
        result: list[str] = []
        for m in geometry:
            if not m.applicationId:
                raise ValueError("geometry with no applicationId cannot be proxied ")
            definition_id = f"DEFINITION:{m.applicationId}"
            result.append(definition_id)
            self._add_definition(definition_id, [m.applicationId], 0)
            self._instance_geometry[m.applicationId] = m

        return result

    def _add_definition(
        self, definition_id: str, objects: list[str], max_depth: int
    ) -> None:
        proxy = InstanceDefinitionProxy(
            applicationId=definition_id,
            name=definition_id,
            objects=objects,
            maxDepth=max_depth,
        )
        self._instance_definition_proxies[definition_id] = proxy
