import contextlib
import re
from typing import Dict
from warnings import warn

from gql import Client
from gql.transport.exceptions import TransportServerError
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.websockets import WebsocketsTransport

from specklepy.core.api.credentials import Account
from specklepy.core.api.resources import (
    ActiveUserResource,
    ModelResource,
    OtherUserResource,
    ProjectInviteResource,
    ProjectResource,
    ServerResource,
    SubscriptionResource,
    VersionResource,
    WorkspaceResource,
)
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning


class SpeckleClient:
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
    from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
    from specklepy.api.credentials import get_default_account

    # initialise the client
    client = SpeckleClient(host="app.speckle.systems") # or whatever your host is
    # client = SpeckleClient(host="localhost:3000", use_ssl=False) or use local server

    # authenticate the client with an account
    # (account has been added in Speckle Manager)
    account = get_default_account()
    client.authenticate_with_account(account)

    # create a new project
    input = ProjectCreateInput(name="a shiny new project")
    project = self.project.create(input)

    # or, use a project id to get an existing project from the server
    new_stream = client.project.get("abcdefghij")
    ```
    """

    DEFAULT_HOST = "app.speckle.systems"
    USE_SSL = True

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        use_ssl: bool = USE_SSL,
        verify_certificate: bool = True,
        connection_retries: int = 3,
        connection_timeout: int = 10,
    ) -> None:
        ws_protocol = "ws"
        http_protocol = "http"

        if use_ssl:
            ws_protocol = "wss"
            http_protocol = "https"

        # sanitise host input by removing protocol and trailing slash
        host = re.sub(r"((^\w+:|^)\/\/)|(\/$)", "", host)

        self.url = f"{http_protocol}://{host}"
        self.graphql = f"{self.url}/graphql"
        self.ws_url = f"{ws_protocol}://{host}/graphql"
        self.account = Account()
        self.verify_certificate = verify_certificate
        self.connection_retries = connection_retries
        self.connection_timeout = connection_timeout

        self.httpclient = Client(
            transport=RequestsHTTPTransport(
                url=self.graphql,
                verify=self.verify_certificate,
                retries=self.connection_retries,
                timeout=self.connection_timeout,
            )
        )
        self.wsclient = None

        self._init_resources()

        # ? Check compatibility with the server
        # - i think we can skip this at this point? save a request
        # try:
        #     server_info = self.server.get()
        #     if isinstance(server_info, Exception):
        #         raise server_info
        #     if not isinstance(server_info, ServerInfo):
        #         raise Exception("Couldn't get ServerInfo")
        # except Exception as ex:
        #     raise SpeckleException(
        #         f"{self.url} is not a compatible Speckle Server", ex
        #     ) from ex

    def __repr__(self):
        return (
            f"SpeckleClient( server: {self.url}, authenticated:"
            f" {self.account.token is not None} )"
        )

    def authenticate_with_token(self, token: str) -> None:
        """
        Authenticate the client using a personal access token.
        The token is saved in the client object and a synchronous GraphQL
        entrypoint is created

        Arguments:
            token {str} -- an api token
        """
        self.account = Account.from_token(token, self.url)
        self._set_up_client()

    def authenticate_with_account(self, account: Account) -> None:
        """Authenticate the client using an Account object
        The account is saved in the client object and a synchronous GraphQL
        entrypoint is created

        Arguments:
            account {Account} -- the account object which can be found with
            `get_default_account` or `get_local_accounts`
        """
        self.account = account
        self._set_up_client()

    def _set_up_client(self) -> None:
        headers = {
            "Authorization": f"Bearer {self.account.token}",
            "Content-Type": "application/json",
            "apollographql-client-name": metrics.HOST_APP,
            "apollographql-client-version": metrics.HOST_APP_VERSION,
        }
        httptransport = RequestsHTTPTransport(
            url=self.graphql, headers=headers, verify=self.verify_certificate, retries=3
        )
        wstransport = WebsocketsTransport(
            url=self.ws_url,
            init_payload={"Authorization": f"Bearer {self.account.token}"},
        )
        self.httpclient = Client(transport=httptransport)
        self.wsclient = Client(transport=wstransport)

        self._init_resources()

        try:
            _ = self.active_user.get()
        except SpeckleException as ex:
            if isinstance(ex.exception, TransportServerError):
                if ex.exception.code == 403:
                    warn(
                        SpeckleWarning(
                            "Possibly invalid token - could not authenticate "
                            f"Speckle Client for server {self.url}"
                        ),
                        stacklevel=2,
                    )
                else:
                    raise ex

    def execute_query(self, query: str) -> Dict:
        return self.httpclient.execute(query)

    def _init_resources(self) -> None:
        self.server = ServerResource(
            account=self.account, basepath=self.url, client=self.httpclient
        )

        server_version = None
        with contextlib.suppress(Exception):
            server_version = self.server.version()

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
        self.workspace = WorkspaceResource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.subscription = SubscriptionResource(
            account=self.account,
            basepath=self.ws_url,
            client=self.wsclient,
        )
