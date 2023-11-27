from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# following imports seem to be unnecessary, but they need to stay
# to not break the scripts using these functions as non-core
from specklepy.core.api.models import (
    Activity,
    ActivityCollection,
    Branch,
    Branches,
    Collaborator,
    Commit,
    Commits,
    LimitedUser,
    Object,
    PendingStreamCollaborator,
    ServerInfo,
    Stream,
    Streams,
    User,
)
