from deprecated import deprecated

from specklepy.core.api.models import FE1_DEPRECATION_VERSION
from specklepy.core.api.resources.active_user_resource import ActiveUserResource


@deprecated(
    reason="Class renamed to ActiveUserResource", version=FE1_DEPRECATION_VERSION
)
class Resource(ActiveUserResource):
    """
    Class renamed to ActiveUserResource
    """

    pass
