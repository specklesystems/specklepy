import contextlib
import getpass
import hashlib
import logging
import platform
import queue
import sys
import threading
from typing import Any

import requests

from specklepy.core.api.credentials import Account

"""
Anonymous telemetry to help us understand how to make a better Speckle.
This really helps us to deliver a better open source project and product!
"""
TRACK = True
HOST_APP = "python"
HOST_APP_VERSION = f"python {'.'.join(map(str, sys.version_info[:2]))}"
PLATFORMS = {"win32": "Windows", "cygwin": "Windows", "darwin": "Mac OS X"}

LOG = logging.getLogger(__name__)
METRICS_TRACKER = None

# actions
SDK = "SDK Action"
CONNECTOR = "Connector Action"
RECEIVE = "Receive"
SEND = "Send"


def disable():
    global TRACK
    TRACK = False


def enable():
    global TRACK
    TRACK = True


def set_host_app(host_app: str, host_app_version: str | None = None):
    global HOST_APP, HOST_APP_VERSION
    HOST_APP = host_app
    HOST_APP_VERSION = host_app_version or HOST_APP_VERSION


def track(
    action: str,
    account: Account | None = None,
    custom_props: dict | None = None,
    send_sync: bool = False,
):
    if not TRACK:
        return

    tracker = initialise_tracker(account)
    event_params: dict[str, Any] = {
        "event": action,
        "properties": {
            "distinct_id": tracker.last_user,
            "server_id": tracker.last_server,
            "token": tracker.analytics_token,
            "hostApp": HOST_APP,
            "hostAppVersion": HOST_APP_VERSION,
            "$os": tracker.platform,
            "type": "action",
        },
    }
    if custom_props:
        event_params["properties"].update(custom_props)

    if send_sync:
        tracker.send_event(event_params)
    else:
        tracker.queue_event(event_params)


def initialise_tracker(account: Account | None = None) -> "MetricsTracker":
    global METRICS_TRACKER
    if not METRICS_TRACKER:
        METRICS_TRACKER = MetricsTracker()

    if account:
        METRICS_TRACKER.set_last_user(account.userInfo.email)
        METRICS_TRACKER.set_last_server(account.serverInfo.url)

    return METRICS_TRACKER


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class MetricsTracker(metaclass=Singleton):
    analytics_url: str = "https://analytics.speckle.systems/track?ip=1"
    analytics_token: str = "acd87c5a50b56df91a795e999812a3a4"
    last_user: str = ""
    last_server: str | None = None
    platform: str

    _sending_thread: threading.Thread
    _queue: queue.Queue[dict[str, Any]] = queue.Queue(1000)
    _session = requests.Session()

    def __init__(self) -> None:
        self._sending_thread = threading.Thread(
            target=self._send_tracking_requests, daemon=True
        )
        self.platform = PLATFORMS.get(sys.platform, "linux")
        self._sending_thread.start()
        with contextlib.suppress(Exception):
            node, user = platform.node(), getpass.getuser()
            if node and user:
                self.last_user = f"@{self.hash(f'{node}-{user}')}"

    def set_last_user(self, email: str | None) -> None:
        if not email:
            return
        self.last_user = f"@{self.hash(email)}"

    def set_last_server(self, server: str | None) -> None:
        if not server:
            return
        self.last_server = self.hash(server)

    def hash(self, value: str) -> str:
        inputList = value.lower().split("://")
        input = inputList[len(inputList) - 1].split("/")[0].split("?")[0]
        return hashlib.md5(input.encode("utf-8")).hexdigest().upper()

    def queue_event(self, event_params: dict[str, Any]) -> None:
        try:
            self._queue.put_nowait(event_params)
        except queue.Full:
            LOG.warning(
                "Metrics event was skipped because the metrics queue was was full",
                exc_info=True,
            )

    def send_event(self, event_params: dict[str, Any]) -> None:
        response = self._session.post(self.analytics_url, json=[event_params])
        response.raise_for_status()

    def _send_tracking_requests(self) -> None:
        while True:
            event_params = self._queue.get()

            try:
                self.send_event(event_params)
            except Exception:
                LOG.warning("Error sending metrics request", exc_info=True)

            self._queue.task_done()
