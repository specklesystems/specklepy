import re
from typing import Dict
from warnings import warn

from deprecated import deprecated
from gql import Client
from gql.transport.exceptions import TransportServerError
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.websockets import WebsocketsTransport

from specklepy.api import resources
from specklepy.core.api.credentials import Account, get_account_from_token
from specklepy.api.resources import (
    active_user,
    branch,
    commit,
    object,
    other_user,
    server,
    stream,
    subscriptions,
    user,
)
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning

from specklepy.core.api.client import SpeckleClient 
