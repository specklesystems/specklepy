from typing import List


class SpeckleException(Exception):
    def __init__(self, message: str, exception: Exception = None) -> None:
        self.message = message
        self.exception = exception

    def __repr__(self) -> str:
        return f"SpeckleException: {self.message}"


class GraphQLException(SpeckleException):
    def __init__(self, message: str, errors: List, data=None) -> None:
        super().__init__(message=message)
        self.errors = errors
        self.data = data
