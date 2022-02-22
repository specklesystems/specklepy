import os
import sys
import queue
import hashlib
import logging
import requests
import threading

"""
Anonymous telemetry to help us understand how to make a better Speckle.
This really helps us to deliver a better open source project and product!
"""
TRACK = True
HOST_APP = "python"
PLATFORMS = {"win32": "Windows", "cygwin": "Windows", "darwin": "Mac OS X"}

LOG = logging.getLogger(__name__)
METRICS_TRACKER = None

# actions
RECEIVE = "receive"
SEND = "send"
STREAM_CREATE = "stream/create"
STREAM_GET = "stream/get"
STREAM_UPDATE = "stream/update"
STREAM_DELETE = "stream/delete"
STREAM_DETAILS = "stream/details"
STREAM_LIST = "stream/list"
STREAM_VIEW = "stream/view"
STREAM_SEARCH = "stream/search"

ACCOUNT_DEFAULT = "account/default"
ACCOUNT_DETAILS = "account/details"
ACCOUNT_LIST = "account/list"

SERIALIZE = "serialization/serialize"
DESERIALIZE = "serialization/deserialize"


def disable():
    global TRACK
    TRACK = False


def enable():
    global TRACK
    TRACK = True


def set_host_app(host_app: str):
    global HOST_APP
    HOST_APP = host_app


def track(action: str, email: str = None, server: str = None):
    if not TRACK:
        return
    try:
        initialise_tracker(email, server)
        page_params = {
            "rec": 1,
            "action_name": action,
            "url": f"http://connectors/{HOST_APP}/{action}",
            "urlref": f"http://connectors/{HOST_APP}/{action}",
            "_cvar": {"1": ["hostApplication", HOST_APP]},
        }

        event_params = {
            "rec": 1,
            "_cvar": {"1": ["hostApplication", HOST_APP]},
            "e_c": HOST_APP,
            "e_a": action,
        }

        METRICS_TRACKER.queue.put_nowait([event_params, page_params])
    except Exception as ex:
        # wrapping this whole thing in a try except as we never want a failure here to annoy users!
        LOG.error("Error queueing metrics request: " + str(ex))


def initialise_tracker(email: str = None, server: str = None):
    global METRICS_TRACKER
    if not METRICS_TRACKER:
        METRICS_TRACKER = MetricsTracker()

    if email:
        METRICS_TRACKER.set_last_user(email)
    if server:
        METRICS_TRACKER.set_last_server(server)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MetricsTracker(metaclass=Singleton):
    analytics_url = "https://analytics.speckle.systems"
    analytics_token = "acd87c5a50b56df91a795e999812a3a4"
    host_app = "python"
    last_user = None
    last_server = None
    platform = None
    sending_thread = None
    queue = queue.Queue(1000)

    def __init__(self) -> None:
        self.sending_thread = threading.Thread(
            target=self._send_tracking_requests, daemon=True
        )
        self.platform = PLATFORMS.get(sys.platform, "linux")
        self.sending_thread.start()

    def set_last_user(self, email: str):
        if not email:
            return
        self.last_user = "@" + self.hash(email)

    def set_last_server(self, server: str):
        if not server:
            return
        self.last_server = self.hash(server)

    def hash(self, value: str):
        return hashlib.md5(value.lower().encode("utf-8")).hexdigest().upper()

    def _send_tracking_requests(self):
        session = requests.Session()
        while True:
            params = self.queue.get()

            try:
                session.post(self.analytics_url, params=params[0])
                session.post(self.analytics_url, params=params[1])
            except Exception as ex:
                LOG.error("Error sending metrics request: " + str(ex))

            self.queue.task_done()
