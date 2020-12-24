from typing import List
from speckle.objects.base import Base
from speckle.transports.memory import MemoryTransport
from speckle.logging.exceptions import SpeckleException
from speckle.transports.abstract_transport import AbstractTransport
from speckle.serialization.base_object_serializer import BaseObjectSerializer


def send(
    base: Base,
    transports: List[AbstractTransport] = [],
    use_default_cache: bool = True,
):
    """Sends an object via the provided transports. Defaults to the local cache.

    Arguments:
        obj {Base} -- the object you want to send
        transports {list} -- where you want to send them
        use_default_cache {bool} -- toggle for the default cache. If set to false, it will only send to the provided transports

    Returns:
        str -- the object id of the sent object
    """
    if not transports and not use_default_cache:
        raise SpeckleException(
            message="You need to provide at least one transport: cannot send with an empty transport list and no default cache"
        )
    if use_default_cache:
        # TODO: finish sqlite transport and chuck it in here
        pass

    serializer = BaseObjectSerializer(write_transports=transports)

    for t in transports:
        t.begin_write()
    hash, _ = serializer.write_json(base=base)

    for t in transports:
        t.end_write()

    return hash


def receive(
    obj_id: str,
    remote_transport: AbstractTransport = None,
    local_transport: AbstractTransport = None,
) -> Base:
    """Receives an object from a transport.

    Arguments:
        obj_id {str} -- the id of the object to receive
        remote_transport {Transport} -- the transport to receive from
        local_transport {Transport} -- the transport to send from

    Returns:
        Base -- the base object
    """

    # TODO: replace with sqlite transport
    if not local_transport:
        local_transport = MemoryTransport()

    serializer = BaseObjectSerializer(read_transport=local_transport)

    # try local transport first. if the parent is there, we assume all the children are there and continue wth deserialisation using the local transport
    obj_string = local_transport.get_object(obj_id)
    if obj_string:
        base = serializer.read_json(obj_string=obj_string)
        return base

    if not remote_transport:
        raise SpeckleException(
            message="Could not find the specified object using the local transport, and you didn't provide a fallback remote from which to pull it."
        )

    obj_string = remote_transport.copy_object_and_children(
        id=obj_id, target_transport=local_transport
    )

    return serializer.read_json(obj_string=obj_string)


def serialize(base: Base) -> str:
    serializer = BaseObjectSerializer()

    return serializer.write_json(base)[1]


def deserialize(obj_string: str) -> Base:
    serializer = BaseObjectSerializer()

    return serializer.read_json(obj_string=obj_string)
