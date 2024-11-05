from deprecated import deprecated

from specklepy.api.credentials import Account
from specklepy.api.resources import (
    ActiveUserResource,
    ModelResource,
    OtherUserResource,
    ProjectInviteResource,
    ProjectResource,
    SubscriptionResource,
    VersionResource,
    branch,
    commit,
    object,
    server,
    stream,
    subscriptions,
    user,
)
from specklepy.core.api.client import SpeckleClient as CoreSpeckleClient
from specklepy.logging import metrics


class SpeckleClient(CoreSpeckleClient):
    """
    The `SpeckleClient` is your entry point for interacting with
    your Speckle Server's GraphQL API.
    You'll need to have access to a server to use it,
    or you can use our public server `app.speckle.systems`.

    To authenticate the client, you'll need to have downloaded
    the [Speckle Manager](https://speckle.guide/#speckle-manager)
    and added your account.

    ```py
    from specklepy.api.client import SpeckleClient
    from specklepy.api.credentials import get_default_account

    # initialise the client
    client = SpeckleClient(host="app.speckle.systems") # or whatever your host is
    # client = SpeckleClient(host="localhost:3000", use_ssl=False) or use local server

    # authenticate the client with an account (account has been added in Speckle Manager)
    account = get_default_account()
    client.authenticate_with_account(account)

    # create a new stream. this returns the stream id
    new_stream_id = client.stream.create(name="a shiny new stream")

    # use that stream id to get the stream from the server
    new_stream = client.stream.get(id=new_stream_id)
    ```
    """

    DEFAULT_HOST = "app.speckle.systems"
    USE_SSL = True

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        use_ssl: bool = USE_SSL,
        verify_certificate: bool = True,
    ) -> None:
        super().__init__(
            host=host,
            use_ssl=use_ssl,
            verify_certificate=verify_certificate,
        )
        self.account = Account()

    def _init_resources(self) -> None:
        self.server = server.Resource(
            account=self.account, basepath=self.url, client=self.httpclient
        )

        server_version = None
        try:
            server_version = self.server.version()
        except Exception:
            pass

        self.other_user = OtherUserResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.active_user = ActiveUserResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.project = ProjectResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.project_invite = ProjectInviteResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.model = ModelResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.version = VersionResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.subscription = SubscriptionResource(
            account=self.account,
            basepath=self.ws_url,
            client=self.wsclient,
            # todo: why doesn't this take a server version
        )
        # Deprecated Resources
        self.user = user.Resource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.stream = stream.Resource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.commit = commit.Resource(
            account=self.account, basepath=self.url, client=self.httpclient
        )
        self.branch = branch.Resource(
            account=self.account, basepath=self.url, client=self.httpclient
        )
        self.object = object.Resource(
            account=self.account, basepath=self.url, client=self.httpclient
        )
        self.subscribe = subscriptions.Resource(
            account=self.account,
            basepath=self.ws_url,
            client=self.wsclient,
        )

    @deprecated(
        version="2.6.0",
        reason=(
            "Renamed: please use `authenticate_with_account` or"
            " `authenticate_with_token` instead."
        ),
    )
    def authenticate(self, token: str) -> None:
        """Authenticate the client using a personal access token
        The token is saved in the client object and a synchronous GraphQL
        entrypoint is created

        Arguments:
            token {str} -- an api token
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "Client Authenticate_deprecated"}
        )
        return super().authenticate(token)

    def authenticate_with_token(self, token: str) -> None:
        """
        Authenticate the client using a personal access token.
        The token is saved in the client object and a synchronous GraphQL
        entrypoint is created

        Arguments:
            token {str} -- an api token
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "Client Authenticate With Token"}
        )
        return super().authenticate_with_token(token)

    def authenticate_with_account(self, account: Account) -> None:
        """Authenticate the client using an Account object
        The account is saved in the client object and a synchronous GraphQL
        entrypoint is created

        Arguments:
            account {Account} -- the account object which can be found with
            `get_default_account` or `get_local_accounts`
        """
        metrics.track(
            metrics.SDK, self.account, {"name": "Client Authenticate With Account"}
        )
        return super().authenticate_with_account(account)
