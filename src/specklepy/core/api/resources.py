from warnings import warn

from specklepy.api.resources import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.resources` are now deprecated, import from `specklepy.api.resources` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
