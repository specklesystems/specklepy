from warnings import warn

from specklepy.api.enums import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.enums` are now deprecated, import from `specklepy.api.enums` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
