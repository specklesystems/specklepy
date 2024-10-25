from specklepy.api.models import Stream
from specklepy.core.api.resources.stream import Resource as CoreResource


class Resource(CoreResource):
    """API Access class for projects"""

    def __init__(self, account, basepath, client, server_version) -> None:
        super().__init__(
            account=account,
            basepath=basepath,
            client=client,
            server_version=server_version,
        )

        self.schema = Stream
