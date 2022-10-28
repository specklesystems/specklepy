import re
from warnings import warn
from deprecated import deprecated
from specklepy.api.credentials import Account, get_account_from_token
from specklepy.logging import metrics
from specklepy.logging.exceptions import (
    SpeckleException,
    SpeckleWarning,
)
from typing import Dict

from specklepy.api import resources
from specklepy.api.resources import (
    branch,
    commit,
    stream,
    object,
    server,
    user,
    subscriptions,
    other_user,
    active_user
)
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.websockets import WebsocketsTransport


class SpeckleClient:
    """
    The `SpeckleClient` is your entry point for interacting with your Speckle Server's GraphQL API.
    You'll need to have access to a server to use it, or you can use our public server `speckle.xyz`.

    To authenticate the client, you'll need to have downloaded the [Speckle Manager](https://speckle.guide/#speckle-manager)
    and added your account.

    ```py
    from specklepy.api.client import SpeckleClient
    from specklepy.api.credentials import get_default_account

    # initialise the client
    client = SpeckleClient(host="speckle.xyz") # or whatever your host is
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

    DEFAULT_HOST = "speckle.xyz"
    USE_SSL = True

    def __init__(self, host: str = DEFAULT_HOST, use_ssl: bool = USE_SSL) -> None:
        metrics.track(metrics.CLIENT, custom_props={"name": "create"})
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

        self.httpclient = Client(
            transport=RequestsHTTPTransport(url=self.graphql, verify=True, retries=3)
        )
        self.wsclient = None

        self._init_resources()

        # ? Check compatibility with the server - i think we can skip this at this point? save a request
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
        return f"SpeckleClient( server: {self.url}, authenticated: {self.account.token is not None} )"

    @deprecated(
        version="2.6.0",
        reason="Renamed: please use `authenticate_with_account` or `authenticate_with_token` instead.",
    )
    def authenticate(self, token: str) -> None:
        """Authenticate the client using a personal access token
        The token is saved in the client object and a synchronous GraphQL entrypoint is created

        Arguments:
            token {str} -- an api token
        """
        self.authenticate_with_token(token)
        self._set_up_client()

    def authenticate_with_token(self, token: str) -> None:
        """Authenticate the client using a personal access token
        The token is saved in the client object and a synchronous GraphQL entrypoint is created

        Arguments:
            token {str} -- an api token
        """
        self.account = get_account_from_token(token, self.url)
        metrics.track(metrics.CLIENT, self.account, {"name": "authenticate with token"})
        self._set_up_client()

    def authenticate_with_account(self, account: Account) -> None:
        """Authenticate the client using an Account object
        The account is saved in the client object and a synchronous GraphQL entrypoint is created

        Arguments:
            account {Account} -- the account object which can be found with `get_default_account` or `get_local_accounts`
        """
        metrics.track(metrics.CLIENT, account, {"name": "authenticate with account"})
        self.account = account
        self._set_up_client()

    def _set_up_client(self) -> None:
        metrics.track(metrics.CLIENT, self.account, {"name": "set up client"})
        headers = {
            "Authorization": f"Bearer {self.account.token}",
            "Content-Type": "application/json",
            "apollographql-client-name": metrics.HOST_APP,
            "apollographql-client-version": metrics.HOST_APP_VERSION,
        }
        httptransport = RequestsHTTPTransport(
            url=self.graphql, headers=headers, verify=True, retries=3
        )
        wstransport = WebsocketsTransport(
            url=self.ws_url,
            init_payload={"Authorization": f"Bearer {self.account.token}"},
        )
        self.httpclient = Client(transport=httptransport)
        self.wsclient = Client(transport=wstransport)

        self._init_resources()

        if self.user.get() is None:
            warn(
                SpeckleWarning(
                    f"Possibly invalid token - could not authenticate Speckle Client for server {self.url}"
                )
            )

    def execute_query(self, query: str) -> Dict:
        return self.httpclient.execute(query)

    def _init_resources(self) -> None:
        self.server = server.Resource(
            account=self.account, basepath=self.url, client=self.httpclient
        )
        server_version = None
        try:
            server_version = self.server.version()
        except:
            pass
        self.user = user.Resource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.other_user = other_user.Resource(
            account=self.account,
            basepath=self.url,
            client=self.httpclient,
            server_version=server_version,
        )
        self.active_user = active_user.Resource(
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

    def __getattr__(self, name):
        try:
            attr = getattr(resources, name)
            return attr.Resource(
                account=self.account, basepath=self.url, client=self.httpclient
            )
        except:
            raise SpeckleException(
                f"Method {name} is not supported by the SpeckleClient class"
            )
