from warnings import warn

from specklepy.api.credentials import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.credentials` are now deprecated, import from `specklepy.api.credentials` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
