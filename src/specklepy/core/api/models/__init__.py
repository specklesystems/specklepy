from warnings import warn

from specklepy.api.models import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.models` are now deprecated, import from `specklepy.api.models` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
