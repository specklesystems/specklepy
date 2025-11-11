from specklepy.objects.data_objects import DataObject
from specklepy.objects.proxies import LevelProxy


class LevelProxyManager:
    def __init__(self):
        self._level_proxies: dict[str, LevelProxy] = {}

    @property
    def level_proxies(self):
        return self._level_proxies

    def add_element_level_mapping(
        self, level_data_object: DataObject, element_application_id: str
    ) -> None:
        level_id = level_data_object.applicationId
        assert level_id is not None

        proxy = self._level_proxies.get(level_id, None)
        if proxy is not None:
            proxy.objects.append(element_application_id)
        else:
            self._level_proxies[level_id] = LevelProxy(
                objects=[element_application_id],
                value=level_data_object,
                applicationId=level_id,
            )
