from enum import StrEnum


class ProjectVisibility(StrEnum):
    """Supported project visibility types"""

    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTED = "UNLISTED"
    """Deprecated, use PUBLIC instead"""
    WORKSPACE = "WORKSPACE"


class UserProjectsUpdatedMessageType(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"


class ProjectModelsUpdatedMessageType(StrEnum):
    CREATED = "CREATED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class ProjectUpdatedMessageType(StrEnum):
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class ProjectVersionsUpdatedMessageType(StrEnum):
    CREATED = "CREATED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class ProjectModelIngestionUpdatedMessageType(StrEnum):
    CANCELLATION_REQUESTED = "cancellationRequested"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


class ModelIngestionStatus(StrEnum):
    CANCELLED = "cancelled"
    FAILED = "failed"
    PROCESSING = "processing"
    QUEUED = "queued"
    SUCCESS = "success"
