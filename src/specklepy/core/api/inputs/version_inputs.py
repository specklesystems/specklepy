from warnings import warn

from specklepy.api.inputs.version_inputs import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.inputs.version_inputs` are now deprecated, import from `specklepy.api.inputs.version_inputs` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
