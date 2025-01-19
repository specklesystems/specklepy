from typing import Dict, List

from deprecated import deprecated

from specklepy.core.api.models.deprecated import (
    FE1_DEPRECATION_REASON,
    FE1_DEPRECATION_VERSION,
)
from specklepy.core.api.resources.deprecated.object import Resource as CoreResource
from specklepy.logging import metrics
from specklepy.objects.base import Base


class Resource(CoreResource):
    """API Access class for objects"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
        )
        self.schema = Base

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def get(self, stream_id: str, object_id: str) -> Base:
        """
        Get a stream object

        Arguments:
            stream_id {str} -- the id of the stream for the object
            object_id {str} -- the hash of the object you want to get

        Returns:
            Base -- the returned Base object
        """
        metrics.track(metrics.SDK, self.account, {"name": "Object Get"})
        return super().get(stream_id, object_id)

    @deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
    def create(self, stream_id: str, objects: List[Dict]) -> str:
        """
        Not advised - generally, you want to use `operations.send()`.

        Create a new object on a stream.
        To send a base object, you can prepare it by running it through the
        `BaseObjectSerializer.traverse_base()` function to get a valid (serialisable)
        object to send.

        NOTE: this does not create a commit - you can create one with
        `SpeckleClient.commit.create`.
        Dynamic fields will be located in the 'data' dict of the received `Base` object

        Arguments:
            stream_id {str} -- the id of the stream you want to send the object to
            objects {List[Dict]}
            -- a list of base dictionary objects (NOTE: must be json serialisable)

        Returns:
            str -- the id of the object
        """
        metrics.track(metrics.SDK, self.account, {"name": "Object Create"})
        return super().create(stream_id, objects)
