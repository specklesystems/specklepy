import sys
import queue
import hashlib
import getpass
import logging
import requests
import threading
import platform
import contextlib


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
RECEIVE = "Receive"
SEND = "Send"
STREAM = "Stream Action"
PERMISSION = "Permission Action"
COMMIT = "Commit Action"
BRANCH = "Branch Action"
USER = "User Action"
SERVER = "Server Action"
CLIENT = "Speckle Client"
STREAM_WRAPPER = "Stream Wrapper"

ACCOUNTS = "Get Local Accounts"

SERIALIZE = "serialization/serialize"
DESERIALIZE = "serialization/deserialize"


def disable():
    global TRACK
    TRACK = False


def enable():
    global TRACK
    TRACK = True


def set_host_app(host_app: str, host_app_version: str = None):
    global HOST_APP, HOST_APP_VERSION
    HOST_APP = host_app
    HOST_APP_VERSION = host_app_version or HOST_APP_VERSION


def track(action: str, account: "Account" = None, custom_props: dict = None):
    if not TRACK:
        return
    try:
        initialise_tracker(account)
        event_params = {
            "event": action,
            "properties": {
                "distinct_id": METRICS_TRACKER.last_user,
                "server_id": METRICS_TRACKER.last_server,
                "token": METRICS_TRACKER.analytics_token,
                "hostApp": HOST_APP,
                "hostAppVersion": HOST_APP_VERSION,
                "$os": METRICS_TRACKER.platform,
                "type": "action",
            },
        }
        if custom_props:
            event_params["properties"].update(custom_props)

        METRICS_TRACKER.queue.put_nowait(event_params)
        METRICS_TRACKER.tracked = True
    except Exception as ex:
        # wrapping this whole thing in a try except as we never want a failure here to annoy users!
        LOG.error(f"Error queueing metrics request: {str(ex)}")

def alias_ids(old_id: str, new_id: str):
    if not TRACK:
        return
    try:
        event_params = {
            "event": "$create_alias",
            "properties": {
                "distinct_id": old_id,
                "alias": new_id,
                "token": METRICS_TRACKER.analytics_token,
            },
        }

        METRICS_TRACKER.queue.put_nowait(event_params)
    except Exception as ex:
        LOG.error(f"Error queueing metrics request: {str(ex)}")


def initialise_tracker(account: "Account" = None):
    global METRICS_TRACKER
    if not METRICS_TRACKER:
        METRICS_TRACKER = MetricsTracker()

    if account and account.userInfo.email:
        METRICS_TRACKER.set_last_user(account.userInfo.email)
    if account and account.serverInfo.url:
        METRICS_TRACKER.set_last_server(account.userInfo.email)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MetricsTracker(metaclass=Singleton):
    analytics_url = "https://analytics.speckle.systems/track?ip=1"
    alias_ids_url = "https://api.mixpanel.com/track#identity-create-alias?strict=1"
    analytics_token = "acd87c5a50b56df91a795e999812a3a4"
    last_user = ""
    last_server = None
    platform = None
    sending_thread = None
    queue = queue.Queue(1000)
    tracked = False

    def __init__(self) -> None:
        self.sending_thread = threading.Thread(
            target=self._send_tracking_requests, daemon=True
        )
        self.platform = PLATFORMS.get(sys.platform, "linux")
        self.sending_thread.start()
        with contextlib.suppress(Exception):
            node, user = platform.node(), getpass.getuser()
            if node and user:
                self.last_user = f"@{self.hash(f'{node}-{user}')}"

    def set_last_user(self, email: str):
        if not email:
            return
        new_id = f"@{self.hash(email)}"
        if self.tracked and self.last_user and new_id != self.last_user:
            alias_ids(self.last_user, new_id)
        self.last_user = new_id

    def set_last_server(self, server: str):
        if not server:
            return
        self.last_server = self.hash(server)

    def hash(self, value: str):
        return hashlib.md5(value.lower().encode("utf-8")).hexdigest().upper()

    def _send_tracking_requests(self):
        session = requests.Session()
        while True:
            event_params = [self.queue.get()]

            post_url = self.alias_ids_url if event_params[0]['event'] == "$create_alias" else self.analytics_url

            try:
                session.post(post_url, json=event_params)
            except Exception as ex:
                LOG.error(f"Error sending metrics request: {str(ex)}")

            self.queue.task_done()