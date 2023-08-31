from typing import Dict, List

from gql import gql

from specklepy.core.api.resource import ResourceBase
from specklepy.objects.base import Base

NAME = "object"


class Resource(ResourceBase):
    """API Access class for objects"""

    def __init__(self, account, basepath, client) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            name=NAME,
        )
        self.schema = Base

    def get(self, stream_id: str, object_id: str) -> Base:
        """
        Get a stream object

        Arguments:
            stream_id {str} -- the id of the stream for the object
            object_id {str} -- the hash of the object you want to get

        Returns:
            Base -- the returned Base object
        """
        query = gql(
            """
            query Object($stream_id: String!, $object_id: String!) {
              stream(id: $stream_id) {
                id
                name
                object(id: $object_id) {
                  id
                  speckleType
                  applicationId
                  createdAt
                  totalChildrenCount
                  data
                }
              }
            }
          """
        )
        params = {"stream_id": stream_id, "object_id": object_id}

        return self.make_request(
            query=query,
            params=params,
            return_type=["stream", "object", "data"],
        )

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
        query = gql(
            """
          mutation ObjectCreate($object_input: ObjectCreateInput!) {
            objectCreate(objectInput: $object_input)
        }
          """
        )
        params = {"object_input": {"streamId": stream_id, "objects": objects}}

        return self.make_request(
            query=query, params=params, return_type="objectCreate", parse_response=False
        )
