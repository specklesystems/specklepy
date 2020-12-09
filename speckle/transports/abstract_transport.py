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
    def get_object(self, id: str) -> str or None:
        """Gets an object. Returns `None` if the object is not found.

        Arguments:
            id {str} -- the hash of the object

        Returns:
            str -- the full string representation of the object (or null if no object is found)
        """
        pass

    @abstractmethod
    def copy_object_and_children(self, id: str, target_transport: Transport) -> str:
        """Copies the parent object and all its children to the provided transport.

        Arguments:
            id {str} -- the id of the object you want to copy
            target_transport {AbstractTransport} -- the transport you want to copy the object to
        Returns:
            str -- the string representation of the root object
        """
        pass
