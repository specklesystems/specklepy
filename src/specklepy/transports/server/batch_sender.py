import gzip
import json
import logging
import queue
import threading

import requests

from specklepy.logging.exceptions import SpeckleException

LOG = logging.getLogger(__name__)


class BatchSender(object):
    def __init__(
        self,
        server_url,
        stream_id,
        token,
        max_batch_size_mb=1,
        max_batch_length=20000,
        batch_buffer_length=10,
        thread_count=4,
    ):
        self.server_url = server_url
        self.stream_id = stream_id
        self._token = token

        self.max_size = int(max_batch_size_mb * 1000 * 1000)
        self.max_batch_length = int(max_batch_length)
        self._batches = queue.Queue(batch_buffer_length)
        self._crt_batch = []
        self._crt_batch_size = 0

        self.thread_count = thread_count
        self._send_threads = []
        self._exception = None

    def send_object(self, id: str, obj: str):
        if not self._send_threads:
            self._create_threads()

        crt_obj_size = len(obj)
        crt_batch_length = len(self._crt_batch)
        if not self._crt_batch or (
            self._crt_batch_size + crt_obj_size < self.max_size
            and crt_batch_length < self.max_batch_length
        ):
            self._crt_batch.append((id, obj))
            self._crt_batch_size += crt_obj_size
            return

        self._batches.put(self._crt_batch)
        self._crt_batch = [(id, obj)]
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

    def _bg_send_batch(self, session: requests.Session, batch):
        object_ids = [obj[0] for obj in batch]
        response = session.post(
            url=f"{self.server_url}/api/diff/{self.stream_id}",
            data={"objects": json.dumps(object_ids)},
        )
        if response.status_code == 403:
            raise SpeckleException(
                f"Invalid credentials - cannot send objects to server {self.server_url}"
            )
        response.raise_for_status()
        server_has_object = response.json()

        new_object_ids = [x for x in object_ids if not server_has_object[x]]
        new_object_ids = set(new_object_ids)
        new_objects = [obj[1] for obj in batch if obj[0] in new_object_ids]

        if not new_objects:
            LOG.info(
                f"Uploading batch of {len(batch)} objects: all objects are already in"
                " the server"
            )
            return

        upload_data = "[" + ",".join(new_objects) + "]"
        upload_data_gzip = gzip.compress(upload_data.encode())
        LOG.info(
            "Uploading batch of %s objects (%s new): (size: %s, compressed size: %s)"
            % (len(batch), len(new_objects), len(upload_data), len(upload_data_gzip))
        )

        try:
            r = session.post(
                url=f"{self.server_url}/objects/{self.stream_id}",
                files={"batch-1": ("batch-1", upload_data_gzip, "application/gzip")},
            )
            if r.status_code != 201:
                LOG.warning("Upload server response: %s", r.text)
                raise SpeckleException(
                    message=(
                        "Could not save the object to the server - status code"
                        f" {r.status_code} ({r.text[:1000]})"
                    )
                )
        except json.JSONDecodeError as error:
            return SpeckleException(
                f"Failed to send objects to {self.server_url}. Please ensure this"
                f" stream ({self.stream_id}) exists on this server and that you have"
                " permission to send to it.",
                error,
            )

    def _create_threads(self):
        for _ in range(self.thread_count):
            t = threading.Thread(target=self._sending_thread_main, daemon=True)
            t.start()
            self._send_threads.append(t)

    def _delete_threads(self):
        for _ in range(len(self._send_threads)):
            self._batches.put(None)

        for thread in self._send_threads:
            thread.join()

        self._send_threads = []

    def __del__(self):
        self._delete_threads()
