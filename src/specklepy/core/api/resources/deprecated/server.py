from deprecated import deprecated

from specklepy.core.api.models.deprecated import FE1_DEPRECATION_VERSION
from specklepy.core.api.resources import ServerResource

NAME = "server"


@deprecated(reason="Renamed to ServerResource", version=FE1_DEPRECATION_VERSION)
class Resource(ServerResource):
    """API Access class for the server"""
