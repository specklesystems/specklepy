from warnings import warn

from specklepy.api.operations import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.operations` are now deprecated, import from `specklepy.api.operations`` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
