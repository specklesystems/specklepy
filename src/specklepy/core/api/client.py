from warnings import warn

from specklepy.api.client import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.client` are now deprecated, import from `specklepy.api.client`` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
