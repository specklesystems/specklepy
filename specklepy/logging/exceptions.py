from typing import Any, List, Optional


class SpeckleException(Exception):
    def __init__(self, message: str, exception: Exception = None) -> None:
        super().__init__()
        self.message = message
        self.exception = exception

    def __str__(self) -> str:
        return f"SpeckleException: {self.message}"


class SpeckleInvalidUnitException(SpeckleException):
    def __init__(self, invalid_unit: Any) -> None:

        super().__init__(
            message=f"Invalid units: expected type str but received {type(invalid_unit)} ({invalid_unit}).",
            exception=None,
        )


class SerializationException(SpeckleException):
    def __init__(self, message: str, obj: Any, exception: Exception = None) -> None:
        super().__init__(message=message, exception=exception)
        self.obj = obj
        self.unhandled_type = type(obj)

    def __str__(self) -> str:
        return f"SpeckleException: Could not serialize object of type {self.unhandled_type}"


class GraphQLException(SpeckleException):
    def __init__(
        self, message: str, errors: Optional[List[Any]] = None, data=None
    ) -> None:
        super().__init__(message=message)
        self.errors = errors
        self.data = data

    def __str__(self) -> str:
        return f"GraphQLException: {self.message}"


class UnsupportedException(SpeckleException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message)

    def __str__(self) -> str:
        return f"UnsupportedException: {self.message}"


class SpeckleWarning(Warning):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
