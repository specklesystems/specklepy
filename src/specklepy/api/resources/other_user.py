from deprecated import deprecated

from specklepy.api.resources.other_user_resource import OtherUserResource
from specklepy.core.api.models import FE1_DEPRECATION_VERSION


@deprecated(reason="Renamed to OtherUserResource", version=FE1_DEPRECATION_VERSION)
class Resource(OtherUserResource):
    """
    Renamed to OtherUserResource
    """
