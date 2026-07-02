from warnings import warn

from specklepy.api.connector_versions import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.connector_versions` are now deprecated, import from `specklepy.api.connector_versions` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
