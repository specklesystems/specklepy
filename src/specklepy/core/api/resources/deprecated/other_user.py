from deprecated import deprecated

from specklepy.core.api.models.deprecated import FE1_DEPRECATION_VERSION
from specklepy.core.api.resources import OtherUserResource


@deprecated(
    reason="Class renamed to OtherUserResource", version=FE1_DEPRECATION_VERSION
)
class Resource(OtherUserResource):
    """
    Class renamed to OtherUserResource
    """

    pass
