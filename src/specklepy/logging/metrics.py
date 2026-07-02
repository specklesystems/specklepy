import importlib.metadata
import logging
import platform
import queue
import sys
import threading
from typing import Any, Literal
from urllib.parse import urlparse

import requests

from specklepy.api.credentials import Account

"""
Lightweight usage telemetry to help us understand how to make a better Speckle.
This really helps us to deliver a better open source project and product!
"""
TRACK = True
HOST_APP = "python"
HOST_APP_VERSION = f"python {'.'.join(map(str, sys.version_info[:2]))}"
PLATFORMS = {"win32": "Windows", "cygwin": "Windows", "darwin": "Mac OS X"}

LOG = logging.getLogger(__name__)
METRICS_TRACKER: "MetricsTracker | None" = None

# actions
RECEIVE = "Receive"
SEND = "Send"
ACTIONS = Literal["Receive", "Send"]


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
    action: ACTIONS,
    account: Account,
    custom_props: dict | None = None,
    send_sync: bool = False,
):
    """
    :param action:
    :type action: ACTIONS
    :param account:
    :type account: Account
    :param custom_props:
    :type custom_props: dict | None
    :param send_sync: When `True`, the track event is executed synchronously,
           and any exceptions will be raised.
           When `False`, the track it is deferred to a queue, and any exceptions will be
           swallowed and reported as warnings.
    :type send_sync: bool
    """
    if not TRACK:
        return

    tracker = _initialise_tracker()
    specklepy_version: str | None = None
    try:
        specklepy_version = importlib.metadata.version("specklepy")
    except importlib.metadata.PackageNotFoundError:
        if send_sync:
            raise
        else:
            LOG.warning("Failed to read specklepy's version number", exc_info=True)

    distinct_id = account.userInfo.id
    event_params: dict[str, Any] = {
        "api_key": tracker.analytics_token,
        "distinct_id": distinct_id,
        "event": action,
        "properties": {
            "$os": tracker.platform,
            "$os_version": platform.version(),
            "$lib": "specklepy",
            "$lib_version": specklepy_version,
            "$user_id": distinct_id,
            "$host": urlparse(account.serverInfo.url).hostname,
            "hostAppSlug": HOST_APP,
            "hostAppVersion": HOST_APP_VERSION,
            "pythonImplementation": platform.python_implementation(),
            "pythonVersion": platform.python_version(),
            "osDescription": platform.platform(),
            "email": account.userInfo.email,
            "specklePyVersion": specklepy_version,
        },
    }
    if custom_props:
        event_params["properties"].update(custom_props)

    if send_sync:
        tracker.send_event(event_params)
    else:
        tracker.queue_event(event_params)


def _initialise_tracker() -> "MetricsTracker":
    global METRICS_TRACKER
    if not METRICS_TRACKER:
        METRICS_TRACKER = MetricsTracker()

    return METRICS_TRACKER


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class MetricsTracker(metaclass=Singleton):
    analytics_url: str = "https://eu.i.posthog.com/i/v0/e/"
    analytics_token: str = "phc_7zaDwBgrBYb1yUe0Ff3Sn0DUibq0NoPNxYNC90M7cfg"
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
