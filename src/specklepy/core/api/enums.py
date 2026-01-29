from enum import Enum


class ProjectVisibility(str, Enum):
    """Supported project visibility types"""

    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTED = "UNLISTED"
    """Deprecated, use PUBLIC instead"""
    WORKSPACE = "WORKSPACE"


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


class ProjectModelIngestionUpdatedMessageType(str, Enum):
    CANCELLATION_REQUESTED = "cancellationRequested"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


class ModelIngestionStatus(str, Enum):
    CANCELLED = "cancelled"
    FAILED = "failed"
    PROCESSING = "processing"
    QUEUED = "queued"
    SUCCESS = "success"
