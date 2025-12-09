from typing import Any, Callable

import pytest
from pytest_httpserver import HTTPServer
from requests import HTTPError
from werkzeug import Request, Response

from specklepy.core.api.client import SpeckleClient
from specklepy.logging import metrics

PATH = "/"


def assert_common_properties(payload: Any) -> None:
    assert payload["event"] == "SDK Action"
    assert payload["properties"]["token"] == "acd87c5a50b56df91a795e999812a3a4"
    assert payload["properties"]["type"] == "action"
    assert payload["properties"]["server_id"]
    assert payload["properties"]["distinct_id"]
    assert payload["properties"]["hostApp"] == "python"
    assert payload["properties"]["hostAppVersion"]
    assert payload["properties"]["core_version"]


def handler(extra_check: Callable[[Any], bool]) -> Callable[[Request], Response]:
    def inner(request: Request) -> Response:
        json = request.get_json()
        payload = json[0]
        assert_common_properties(payload)
        assert extra_check(payload)
        return Response("", 200)

    return inner


def test_metrics_track(httpserver: HTTPServer, client: SpeckleClient):
    with ScopedMetricsWrapper(httpserver.url_for(PATH)) as _:
        # Test No email
        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(lambda payload: "email" not in payload["properties"])
        )
        metrics.track("SDK Action", client.account, None, True, False)

        # Test With email
        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(
                lambda payload: payload["properties"]["email"]
                == client.account.userInfo.email
            )
        )
        metrics.track("SDK Action", client.account, None, True, True)

        # Test With custom value
        httpserver.expect_oneshot_request(PATH, "post").respond_with_handler(
            handler(
                lambda payload: payload["properties"]["myCustomProp"] == "myCustomValue"
            )
        )
        metrics.track(
            "SDK Action", client.account, {"myCustomProp": "myCustomValue"}, True, True
        )


def test_metrics_errors(httpserver: HTTPServer):
    with ScopedMetricsWrapper(httpserver.url_for(PATH)) as _:
        httpserver.expect_oneshot_request(PATH, "post").respond_with_data("", 400)

        # Expect send_sync == true to mean mean it will raise
        with pytest.raises(HTTPError):
            metrics.track("SDK Action", send_sync=True)

        # Expect send_sync == false to mean mean it won't
        metrics.track("SDK Action")


class ScopedMetricsWrapper:
    tracker: metrics.MetricsTracker

    def __init__(self, metrics_url: str):
        self.tracker = metrics.initialise_tracker()
        self.tracker.analytics_url = metrics_url

    def __enter__(self):
        # Setup
        metrics.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        metrics.disable()
        metrics.METRICS_TRACKER = None
