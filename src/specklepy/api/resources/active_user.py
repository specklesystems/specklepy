from deprecated import deprecated

from specklepy.api.resources.active_user_resource import ActiveUserResource
from specklepy.core.api.models import FE1_DEPRECATION_VERSION


@deprecated(reason="Renamed to ActiveUserResource", version=FE1_DEPRECATION_VERSION)
class Resource(ActiveUserResource):
    """Renamed to ActiveUserResource"""
