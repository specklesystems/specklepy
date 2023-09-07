from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractTransport(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def begin_write(self) -> None:
        """Optional: signals to the transport that writes are about to begin."""
        pass

    @abstractmethod
    def end_write(self) -> None:
        """
        Optional: signals to the transport that no more items will need to be written.
        """
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
    def save_object_from_transport(
        self, id: str, source_transport: "AbstractTransport"
    ) -> None:
        """Saves an object from the given source transport.

        Arguments:
            id {str} -- the hash of the object
            source_transport {AbstractTransport)
            -- the transport through which the object can be found
        """
        pass

    @abstractmethod
    def get_object(self, id: str) -> Optional[str]:
        """Gets an object. Returns `None` if the object is not found.

        Arguments:
            id {str} -- the hash of the object

        Returns:
            str -- the full string representation
            of the object (or null if no object is found)
        """
        pass

    @abstractmethod
    def has_objects(self, id_list: List[str]) -> Dict[str, bool]:
        """Checks the presence of multiple objects.

        Arguments:
            id_list -- List of object id to be checked

        Returns:
            Dict[str, bool] -- keys: input ids, values:
                whether the transport has that object
        """
        pass

    @abstractmethod
    def copy_object_and_children(
        self, id: str, target_transport: "AbstractTransport"
    ) -> str:
        """Copies the parent object and all its children to the provided transport.

        Arguments:
            id {str} -- the id of the object you want to copy
            target_transport {AbstractTransport}
                -- the transport you want to copy the object to
        Returns:
            str -- the string representation of the root object
        """
        pass
