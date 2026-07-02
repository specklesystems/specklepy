from warnings import warn

from specklepy.api.models.subscription_messages import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.models.subscription_messages` are now deprecated, import from `specklepy.api.models.subscription_messages` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
