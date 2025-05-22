from enum import Enum


class ProjectVisibility(str, Enum):
    """Supported project visibility types"""

    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTED = "UNLISTED"
    WORKSPACE = "WORKSPACE"


foo = ProjectVisibility.PRIVATE


class UserProjectsUpdatedMessageType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"


class ProjectModelsUpdatedMessageType(str, Enum):
    CREATED = "CREATED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class ProjectUpdatedMessageType(str, Enum):
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class ProjectVersionsUpdatedMessageType(str, Enum):
    CREATED = "CREATED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"
