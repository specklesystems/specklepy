import os
import queue
import logging
import requests
import threading
from requests.sessions import session
from specklepy.transports.sqlite import SQLiteTransport

"""
Anonymous telemetry to help us understand how to make a better Speckle.
This really helps us to deliver a better open source project and product!
"""
TRACK = True
HOST_APP = "python"

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


def set_host_app(host_app: str):
    global HOST_APP
    HOST_APP = host_app


def track(action: str):
    if not TRACK:
        return
    try:
        global METRICS_TRACKER
        if not METRICS_TRACKER:
            METRICS_TRACKER = MetricsTracker()

        page_params = {
            "rec": 1,
            "idsite": METRICS_TRACKER.site_id,
            "uid": METRICS_TRACKER.suuid,
            "action_name": action,
            "url": f"http://connectors/{HOST_APP}/{action}",
            "urlref": f"http://connectors/{HOST_APP}/{action}",
            "_cvar": {"1": ["hostApplication", HOST_APP]},
        }

        event_params = {
            "rec": 1,
            "idsite": METRICS_TRACKER.site_id,
            "uid": MetricsTracker.suuid,
            "_cvar": {"1": ["hostApplication", HOST_APP]},
            "e_c": HOST_APP,
            "e_a": action,
        }

        METRICS_TRACKER.queue.put_nowait([event_params, page_params])
    except Exception as ex:
        # wrapping this whole thing in a try except as we never want a failure here to annoy users!
        LOG.error("Error queueing metrics request: " + str(ex))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MetricsTracker(metaclass=Singleton):
    matomo_url = "https://speckle.matomo.cloud/matomo.php"
    site_id = 2
    host_app = "python"
    suuid = None
    sending_thread = None
    queue = queue.Queue(1000)

    def __init__(self) -> None:
        self.sending_thread = threading.Thread(
            target=self._send_tracking_requests, daemon=True
        )
        self.set_suuid()
        self.sending_thread.start()

    def set_suuid(self):
        try:
            file_path = os.path.join(SQLiteTransport.get_base_path("Speckle"), "suuid")
            with open(file_path, "r") as file:
                self.suuid = file.read()
        except:
            self.suuid = "unknown-suuid"

    def _send_tracking_requests(self):
        session = requests.Session()
        while True:
            params = self.queue.get()

            try:
                session.post(self.matomo_url, params=params[0])
                session.post(self.matomo_url, params=params[1])
            except Exception as ex:
                LOG.error("Error sending metrics request: " + str(ex))

            self.queue.task_done()
