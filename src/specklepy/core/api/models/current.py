from warnings import warn

from specklepy.api.models.current import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.models.current` are now deprecated, import from `specklepy.api.models.current` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
