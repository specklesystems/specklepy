from typing import Any, List


class SpeckleException(Exception):
    def __init__(self, message: str, exception: Exception = None) -> None:
        self.message = message
        self.exception = exception

    def __str__(self) -> str:
        return f"SpeckleException: {self.message}"


class SerializationException(SpeckleException):
    def __init__(self, message: str, object: Any, exception: Exception = None) -> None:
        super().__init__(message=message)
        self.object = object
        self.unhandled_type = type(object)

    def __str__(self) -> str:
        return f"SpeckleException: Could not serialize object of type {self.unhandled_type}"


class GraphQLException(SpeckleException):
    def __init__(self, message: str, errors: List, data=None) -> None:
        super().__init__(message=message)
        self.errors = errors
        self.data = data

    def __str__(self) -> str:
        return f"GraphQLException: {self.message}"


class SpeckleWarning(Warning):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)