from deprecated import deprecated

from specklepy.core.api.models.deprecated import FE1_DEPRECATION_VERSION
from specklepy.core.api.resources import ActiveUserResource


@deprecated(
    reason="Class renamed to ActiveUserResource", version=FE1_DEPRECATION_VERSION
)
class Resource(ActiveUserResource):
    """
    Class renamed to ActiveUserResource
    """

    pass
