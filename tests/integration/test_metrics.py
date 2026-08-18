from typing import Any, Callable

import pytest
from pytest_httpserver import HTTPServer
from requests import HTTPError
from werkzeug import Request, Response

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import Account, UserInfo
from specklepy.api.models.current import ServerInfo
from specklepy.logging import metrics

PATH = "/"

TEST_USER_ID = "abcefmyuser"
TEST_USER_EMAIL = "me@example.com"


def assert_common_properties(payload: Any) -> None:
    assert payload["event"] == "Send"
    assert payload["distinct_id"] == TEST_USER_ID
    assert payload["properties"]["$os"]
    assert payload["properties"]["$os_version"]
    assert payload["properties"]["$lib"] == "specklepy"
    assert payload["properties"]["$user_id"] == payload["distinct_id"]
    assert payload["properties"]["$host"] == "app.speckle.systems"
    assert payload["properties"]["email"] == TEST_USER_EMAIL
    assert payload["properties"]["hostAppSlug"] == "python"
    assert payload["properties"]["hostAppVersion"]
    assert payload["properties"]["specklePyVersion"]


@pytest.fixture(scope="session")
def metrics_account() -> Account:
    return Account(
        serverInfo=ServerInfo(url="https://app.speckle.systems"),
        userInfo=UserInfo(id=TEST_USER_ID, email="me@example.com"),
    )


def handler(extra_check: Callable[[Any], bool]) -> Callable[[Request], Response]:
    def inner(request: Request) -> Response:
        json = request.get_json()
        payload = json[0]
        assert_common_properties(payload)
        assert extra_check(payload)
        return Response("", 200)

    return inner


def test_metrics_track(httpserver: HTTPServer, metrics_account: Account):
    with ScopedMetricsSetup(httpserver.url_for(PATH)) as _:
        # Test
        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(
                lambda payload: payload["properties"]["email"]
                == metrics_account.userInfo.email
            )
        )
        metrics.track("Send", metrics_account, None, True)

        # Test With custom value
        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(
                lambda payload: payload["properties"]["myCustomProp"] == "myCustomValue"
            )
        )
        metrics.track("Send", metrics_account, {"myCustomProp": "myCustomValue"}, True)


def test_skip_metrics_track_for_non_app_server(
    httpserver: HTTPServer, client: SpeckleClient
):
    with ScopedMetricsSetup(httpserver.url_for(PATH)) as _:
        was_tracked = False

        def track_handler(payload) -> bool:
            nonlocal was_tracked
            was_tracked = True
            return True

        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(track_handler)
        )

        metrics.track("Send", client.account, None, True)

        assert not was_tracked


def test_metrics_errors(httpserver: HTTPServer, metrics_account: Account):
    with ScopedMetricsSetup(httpserver.url_for(PATH)) as _:
        httpserver.expect_oneshot_request(PATH, "post").respond_with_data("", 400)

        # Expect send_sync == true to mean mean it will raise
        with pytest.raises(HTTPError):
            metrics.track("Send", metrics_account, send_sync=True)

        # Expect send_sync == false to mean mean it won't
        metrics.track("Send", metrics_account)


class ScopedMetricsSetup:
    """
    Scoped setup and tear down for enabling metrics tracking
    """

    tracker: metrics.MetricsTracker

    def __init__(self, metrics_url: str):
        self.tracker = metrics._initialise_tracker()
        self.tracker.analytics_url = metrics_url

    def __enter__(self):
        metrics.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        metrics.disable()
        metrics.METRICS_TRACKER = None
