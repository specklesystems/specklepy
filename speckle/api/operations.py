from speckle.transports.abstract_transport import AbstractTransport
from speckle.objects.base import Base


class Operations:
    def __init__(self) -> None:
        pass

    def send(self, obj: Base, transports: list = [], use_default_cache: bool = True):
        """Sends an object via the provided transports. Defaults to the local cache.

        Arguments:
            obj {Base} -- the object you want to send
            transports {list} -- where you want to send them
            use_default_cache {bool} -- toggle for the default cache. If set to false, it will only send to the provided transports

        Returns:
            str -- the object id of the sent object
        """
        raise NotImplementedError

    def receive(
        self,
        obj_id: str,
        remote_transport: AbstractTransport,
        local_transport: AbstractTransport,
    ) -> Base:
        """Receives an object from a transport.

        Arguments:
            obj_id {str} -- the id of the object to receive
            remote_transport {Transport} -- the transport to receive from
            local_transport {Transport} -- the transport to send from

        Returns:
            Base -- the base object
        """
        raise NotImplementedError
