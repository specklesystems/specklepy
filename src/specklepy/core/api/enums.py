from enum import Enum


class FileUploadConversionStatus(Enum):
    QUEUED = 0
    PROCESSING = 1
    SUCCESS = 2
    ERROR = 3


class ProjectVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTEd = "UNLISTED"


class ResourceType(str, Enum):
    COMMIT = "COMMIT"
    STREAM = "STREAM"
    OBJECT = "OBJECT"
    COMMENT = "COMMENT"


class UserProjectsUpdatedMessageType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"


class ProjectCommentsUpdatedMessageType(str, Enum):
    ARCHIVED = "ARCHIVED"
    CREATED = "CREATED"
    UPDATED = "UPDATED"


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
