import logging
import threading
import queue
import time
import gzip

import requests
from specklepy.logging.exceptions import SpeckleException

LOG = logging.getLogger(__name__)


class BatchSender(object):
    def __init__(
        self,
        endpoint,
        token,
        max_batch_size_mb=1,
        batch_buffer_length=10,
        thread_count=4,
    ):
        self.endpoint = endpoint
        self._token = token

        self.max_size = int(max_batch_size_mb * 1000 * 1000)
        self._batches = queue.Queue(batch_buffer_length)
        self._crt_batch = []
        self._crt_batch_size = 0

        self.thread_count = thread_count
        self._send_threads = []
        self._exception = None

    def send_object(self, obj: str):
        if not self._send_threads:
            self._create_threads()

        crt_obj_size = len(obj)
        if not self._crt_batch or self._crt_batch_size + crt_obj_size < self.max_size:
            self._crt_batch.append(obj)
            self._crt_batch_size += crt_obj_size
            return

        self._batches.put(self._crt_batch)
        self._crt_batch = [obj]
        self._crt_batch_size = crt_obj_size

    def flush(self):
        # Add current non-complete batch
        if self._crt_batch:
            self._batches.put(self._crt_batch)
            self._crt_batch = []
            self._crt_batch_size = 0
        # Wait for queued batches to be sent
        self._batches.join()
        # End the sending threads
        self._delete_threads()
        # If there was any error, throw the first exception that occurred during upload
        if self._exception is not None:
            ex = self._exception
            self._exception = None
            raise ex

    def _sending_thread_main(self):
        try:
            session = requests.Session()
            session.headers.update(
                {"Authorization": f"Bearer {self._token}", "Accept": "text/plain"}
            )

            while True:
                batch = self._batches.get()

                # None is a sentinel value, meaning the thread should exit gracefully
                if batch is None:
                    self._batches.task_done()
                    break

                try:
                    self._bg_send_batch(session, batch)
                except Exception as ex:
                    self._exception = self._exception or ex
                    LOG.error("Error sending batch of objects to server: " + str(ex))

                self._batches.task_done()
        except Exception as ex:
            self._exception = self._exception or ex
            LOG.error("ServerTransport sending thread error: " + str(ex))

    def _bg_send_batch(self, session, batch):
        upload_data = "[" + ",".join(batch) + "]"
        upload_data_gzip = gzip.compress(upload_data.encode())
        LOG.info(
            "Uploading batch of %s objects (size: %s, compressed size: %s)"
            % (len(batch), len(upload_data), len(upload_data_gzip))
        )

        r = session.post(
            url=self.endpoint,
            files={"batch-1": ("batch-1", upload_data_gzip, "application/gzip")},
        )
        if r.status_code != 201:
            LOG.warning("Upload server response: %s", r.text)
            raise SpeckleException(
                message=f"Could not save the object to the server - status code {r.status_code}"
            )

    def _create_threads(self):
        for i in range(self.thread_count):
            t = threading.Thread(target=self._sending_thread_main, daemon=True)
            t.start()
            self._send_threads.append(t)

    def _delete_threads(self):
        for i in range(len(self._send_threads)):
            self._batches.put(None)

        for thread in self._send_threads:
            thread.join()

        self._send_threads = []

    def __del__(self):
        self._delete_threads()
