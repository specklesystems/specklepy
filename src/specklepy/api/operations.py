from typing import List, Optional

from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.serialization.base_object_serializer import BaseObjectSerializer
from specklepy.transports.abstract_transport import AbstractTransport
from specklepy.transports.sqlite import SQLiteTransport

from specklepy.core.api.operations import (send as core_send,
                                           receive as _untracked_receive,
                                           serialize as core_serialize,
                                           deserialize as core_deserialize)


def send(
    base: Base,
    transports: Optional[List[AbstractTransport]] = None,
    use_default_cache: bool = True,
):
    """Sends an object via the provided transports. Defaults to the local cache.

    Arguments:
        obj {Base} -- the object you want to send
        transports {list} -- where you want to send them
        use_default_cache {bool} -- toggle for the default cache.
        If set to false, it will only send to the provided transports

    Returns:
        str -- the object id of the sent object
    """
    if transports is None:
        metrics.track(metrics.SEND)
    else:
        metrics.track(metrics.SEND, getattr(transports[0], "account", None))

    return core_send(base, transports, use_default_cache)


def receive(
    obj_id: str,
    remote_transport: Optional[AbstractTransport] = None,
    local_transport: Optional[AbstractTransport] = None,
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
    metrics.track(metrics.RECEIVE, getattr(remote_transport, "account", None))
    return _untracked_receive(obj_id, remote_transport, local_transport)


def serialize(base: Base, write_transports: List[AbstractTransport] = []) -> str:
    """
    Serialize a base object. If no write transports are provided,
    the object will be serialized
    without detaching or chunking any of the attributes.

    Arguments:
        base {Base} -- the object to serialize
        write_transports {List[AbstractTransport]}
        -- optional: the transports to write to

    Returns:
        str -- the serialized object
    """
    metrics.track(metrics.SDK, custom_props={"name": "Serialize"})
    return core_serialize(base, write_transports)

def deserialize(
    obj_string: str, read_transport: Optional[AbstractTransport] = None
) -> Base:
    """
    Deserialize a string object into a Base object.

    If the object contains referenced child objects that are not stored in the local db,
    a read transport needs to be provided in order to recompose
    the base with the children objects.

    Arguments:
        obj_string {str} -- the string object to deserialize
        read_transport {AbstractTransport}
            -- the transport to fetch children objects from
                (defaults to SQLiteTransport)

    Returns:
        Base -- the deserialized object
    """
    metrics.track(metrics.SDK, custom_props={"name": "Deserialize"})
    return core_deserialize(obj_string, read_transport)


__all__ = ["receive", "send", "serialize", "deserialize"]
