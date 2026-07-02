from warnings import warn

from specklepy.api.inputs.model_ingestion_inputs import *  # noqa: F403
from specklepy.logging.exceptions import SpeckleWarning

warn(
    "Imports from `specklepy.core.api.inputs.model_ingestion_inputs` are now deprecated, import from `specklepy.api.inputs.model_ingestion_inputs` instead",  # noqa: E501
    SpeckleWarning,
    stacklevel=2,
)
