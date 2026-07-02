from warnings import warn

from specklepy.api.host_applications import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.host_applications` are now deprecated, import from `specklepy.api.host_applications` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
