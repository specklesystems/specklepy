import os
import time
import sqlite3
import sched
from contextlib import closing
from multiprocessing import Process, Queue
from speckle.transports.abstract_transport import AbstractTransport
from speckle.logging.exceptions import SpeckleException


class SQLiteTransport(AbstractTransport):
    _name = "SQLite"
    _root_path: str = None
    _connection: sqlite3.Connection = None
    _is_writing: bool = False
    _queue: Queue = Queue()
    _scheduler = sched.scheduler(time.time, time.sleep)
    _polling_interval = 0.5  # seconds
    app_name: str
    scope: str
    saved_obj_count: int = 0

    def __init__(
        self, base_path: str = None, app_name: str = None, scope: str = None
    ) -> None:
        base_path = base_path or os.getenv("APPDATA")
        self.app_name = app_name or "Speckle"
        self.scope = scope or "Objects"

        os.makedirs(os.path.join(base_path, self.app_name), exist_ok=True)

        self._root_path = os.path.join(
            os.path.join(base_path, self.app_name, f"{self.scope}.db")
        )
        self.__initialise()

    def __repr__(self) -> str:
        return f"SQLiteTransport(app: '{self.app_name}', scope: '{self.scope}')"

    def __write_timer_elapsed(self):
        print("WRITE TIMER ELAPSED")
        proc = Process(target=_run_queue, args=(self._queue, self._root_path))
        proc.start()
        proc.join()

    def __consume_queue(self):
        if self._is_writing or self._queue.empty():
            return
        print("CONSUME QUEUE")
        self._is_writing = True
        while not self._queue.empty():
            data = self._queue.get()
            self.save_object_sync(data[0], data[1])
        self._is_writing = False

        self._scheduler.enter(
            delay=self._polling_interval, priority=1, action=self.__consume_queue
        )
        self._scheduler.run(blocking=True)

    def save_object(self, id: str, serialized_object: str) -> None:
        """Adds an object to the queue and schedules it to be saved.

        Arguments:
            id {str} -- the object id
            serialized_object {str} -- the full string representation of the object
        """
        print("SAVE OBJECT")
        self._queue.put((id, serialized_object))

        self._scheduler.enter(
            delay=self._polling_interval, priority=1, action=self.__consume_queue
        )
        self._scheduler.run(blocking=True)

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        """Adds an object from the given transport to the queue and schedules it to be saved.

        Arguments:
            id {str} -- the object id
            source_transport {AbstractTransport) -- the transport through which the object can be found
        """
        serialized_object = source_transport.get_object(id)
        self._queue.put((id, serialized_object))
        raise NotImplementedError

    def save_object_sync(self, id: str, serialized_object: str) -> None:
        """Directly saves an object into the database.

        Arguments:
            id {str} -- the object id
            serialized_object {str} -- the full string representation of the object
        """
        self.__check_connection()
        try:
            with closing(self._connection.cursor()) as c:
                c.execute(
                    "INSERT OR IGNORE INTO objects(hash, content) VALUES(?,?)",
                    (id, serialized_object),
                )
                self._connection.commit()
        except Exception as e:
            print(e)
            raise e

    def get_object(self, id: str) -> tuple:
        self.__check_connection()
        with closing(self._connection.cursor()) as c:
            row = c.execute(
                "SELECT * FROM objects WHERE hash = ? LIMIT 1", (id,)
            ).fetchone()
        return row

    def begin_write(self):
        self.saved_obj_count = 0

    def close(self):
        """Close the connection to the database"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __initialise(self) -> None:
        self._connection = sqlite3.connect(self._root_path)
        with closing(self._connection.cursor()) as c:
            c.execute(
                """ CREATE TABLE IF NOT EXISTS objects(
                      hash TEXT PRIMARY KEY,
                      content TEXT
                    ) WITHOUT ROWID;"""
            )
            c.execute("PRAGMA journal_mode='wal';")
            c.execute("PRAGMA count_changes=OFF;")
            c.execute("PRAGMA temp_store=MEMORY;")
            self._connection.commit()

    def __check_connection(self):
        if not self._connection:
            self._connection = sqlite3.connect(self._root_path)

    def __del__(self):
        self._connection.close()


def _run_queue(queue: Queue, root_path: str):
    if queue.empty():
        return
    print("RUN QUEUE")
    conn = sqlite3.connect(root_path)
    while not queue.empty():
        data = queue.get()
        with closing(conn.cursor()) as c:
            c.execute(
                "INSERT OR IGNORE INTO objects(hash, content) VALUES(?,?)",
                (data[0], data[1]),
            )
            conn.commit()
    conn.close()
