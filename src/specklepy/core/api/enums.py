from enum import Enum


class ProjectVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTEd = "UNLISTED"


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
