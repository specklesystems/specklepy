from deprecated import deprecated

from specklepy.api.resources import OtherUserResource
from specklepy.core.api.models.deprecated import FE1_DEPRECATION_VERSION


@deprecated(reason="Renamed to OtherUserResource", version=FE1_DEPRECATION_VERSION)
class Resource(OtherUserResource):
    """
    Renamed to OtherUserResource
    """
