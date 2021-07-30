import json
from typing import List
from specklepy.objects.base import Base
from specklepy.transports.sqlite import SQLiteTransport
from specklepy.transports.server import ServerTransport
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.abstract_transport import AbstractTransport
from specklepy.serialization.base_object_serializer import BaseObjectSerializer


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
        transports.insert(0, SQLiteTransport())

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
        local_transport {Transport} -- the local cache to check for existing objects
                                       (defaults to `SQLiteTransport`)

    Returns:
        Base -- the base object
    """

    if not local_transport:
        local_transport = SQLiteTransport()

    serializer = BaseObjectSerializer(read_transport=local_transport)

    # try local transport first. if the parent is there, we assume all the children are there and continue wth deserialisation using the local transport
    obj_string = local_transport.get_object(obj_id)
    if obj_string:
        return serializer.read_json(obj_string=obj_string)

    if not remote_transport:
        raise SpeckleException(
            message="Could not find the specified object using the local transport, and you didn't provide a fallback remote from which to pull it."
        )

    obj_string = remote_transport.copy_object_and_children(
        id=obj_id, target_transport=local_transport
    )

    return serializer.read_json(obj_string=obj_string)


def serialize(base: Base, write_transports: List[AbstractTransport] = []) -> str:
    """
    Serialize a base object. If no write transports are provided, the object will be serialized
    without detaching or chunking any of the attributes.

    Arguments:
        base {Base} -- the object to serialize
        write_transports {List[AbstractTransport]} -- optional: the transports to write to

    Returns:
        str -- the serialized object
    """
    serializer = BaseObjectSerializer(write_transports=write_transports)

    return serializer.write_json(base)[1]


def deserialize(obj_string: str, read_transport: AbstractTransport = None) -> Base:
    """
    Deserialize a string object into a Base object. If the object contains referenced child objects that are not stored in the local db, a read transport needs to be provided in order to recompose the base with the children objects.

    Arguments:
        obj_string {str} -- the string object to deserialize
        read_transport {AbstractTransport} -- the transport to fetch children objects from
                                              (defaults to SQLiteTransport)

    Returns:
        Base -- the deserialized object
    """
    if not read_transport:
        read_transport = SQLiteTransport()

    serializer = BaseObjectSerializer(read_transport=read_transport)

    return serializer.read_json(obj_string=obj_string)
