from enum import Enum


class FileUploadConversionStatus(Enum):
    QUEUED = 0
    PROCESSING = 1
    SUCCESS = 2
    ERROR = 3


class ProjectVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    UNLISTEd = "UNLISTEd"


class ResourceType(str, Enum):
    COMMIT = "COMMIT"
    STREAM = "STREAM"
    OBJECT = "OBJECT"
    COMMENT = "COMMENT"
