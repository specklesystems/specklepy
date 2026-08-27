from warnings import warn

from specklepy.api.resource import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.resource` are now deprecated, import from `specklepy.api.resource` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
