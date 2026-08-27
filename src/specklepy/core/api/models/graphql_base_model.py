from warnings import warn

from specklepy.api.models.graphql_base_model import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.models.graphql_base_model` are now deprecated, import from `specklepy.api.models.graphql_base_model` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
