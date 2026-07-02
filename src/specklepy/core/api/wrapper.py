from warnings import warn

from specklepy.api.wrapper import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.wrapper` are now deprecated, import from `specklepy.api.wrapper`` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
