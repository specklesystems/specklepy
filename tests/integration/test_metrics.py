from typing import Any, Callable

from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from specklepy.core.api.client import SpeckleClient
from specklepy.logging import metrics


def test_metrics_track(httpserver: HTTPServer, client: SpeckleClient):
    extra_assertion: Callable[[Any], bool]

    def handler(request: Request) -> Response:
        json = request.get_json()

        payload = json[0]
        assert payload["event"] == "SDK Action"
        assert payload["properties"]["token"] == "acd87c5a50b56df91a795e999812a3a4"
        assert payload["properties"]["type"] == "action"
        assert payload["properties"]["server_id"]
        assert payload["properties"]["distinct_id"]
        assert payload["properties"]["hostApp"] == "python"
        assert payload["properties"]["hostAppVersion"]
        assert payload["properties"]["core_version"]

        assert extra_assertion(payload)
        return Response("", 200)

    httpserver.expect_request("/", "post").respond_with_handler(handler)
    with ScopedMetricsWrapper(httpserver.url_for("/")) as _:
        # Test No email
        extra_assertion = lambda payload: "email" not in payload["properties"]  # noqa: E731
        metrics.track("SDK Action", client.account, None, True, False)

        # Test With email
        extra_assertion = (  # noqa: E731
            lambda payload: payload["properties"]["email"]
            == client.account.userInfo.email
        )
        metrics.track("SDK Action", client.account, None, True, True)

        # Test With custom value
        extra_assertion = (  # noqa: E731
            lambda payload: payload["properties"]["myCustomProp"] == "myCustomValue"
        )
        metrics.track(
            "SDK Action", client.account, {"myCustomProp": "myCustomValue"}, True, True
        )


def test_metrics_errors(httpserver: HTTPServer, client: SpeckleClient):
    pass


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
