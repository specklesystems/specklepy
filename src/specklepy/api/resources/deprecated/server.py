from deprecated import deprecated

from specklepy.api.resources import ServerResource
from specklepy.core.api.models.deprecated import FE1_DEPRECATION_VERSION


@deprecated(reason="Renamed to ActiveUserResource", version=FE1_DEPRECATION_VERSION)
class Resource(ServerResource):
    """Renamed to ServerResource"""
