from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

#  __________________
# |                  |
# |  this is v wip   |
# |  pls be careful  |
# |__________________|
# (\__/) ||
# (•ㅅ•)  ||
# / 　 づ


class Transport(ABC):
    """Literally just so I can put a type hint in the AbstractTransport. If there is a better way to do this pls lemme know, my dude

    UPDATE: this can be done in 3.7+ with `from __future__ import annotations`, but we are wanting to support 3.6+
    """

    @abstractmethod
    def name(self):
        pass


@dataclass
class AbstractTransport(Transport):
    _name: str = "Abstract"

    @property
    def name(self):
        return type(self)._name

    @abstractmethod
    def begin_write(self) -> None:
        """Optional: signals to the transport that writes are about to begin."""
        pass

    @abstractmethod
    def end_write(self) -> None:
        """Optional: signals to the transport that no more items will need to be written."""
        pass

    @abstractmethod
    def save_object(self, id: str, serialized_object: str) -> None:
        """Saves the given serialized object.

        Arguments:
            id {str} -- the hash of the object
            serialized_object {str} -- the full string representation of the object
        """
        pass

    @abstractmethod
    def save_object_from_transport(self, id: str, source_transport: Transport) -> None:
        """Saves an object from the given source transport.

        Arguments:
            id {str} -- the hash of the object
            source_transport {AbstractTransport) -- the transport through which the object can be found
        """
        pass

    @abstractmethod
    def get_object(self, id: str) -> str:
        """Gets an object

        Arguments:
            id {str} -- the hash of the object

        Returns:
            str -- the full string representation of the object (or null of no object is found)
        """
        pass
