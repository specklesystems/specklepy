import os
import sys
import time
import sched
import sqlite3
from typing import Any, List, Dict
from appdirs import user_data_dir
from contextlib import closing
from specklepy.transports.abstract_transport import AbstractTransport
from specklepy.logging.exceptions import SpeckleException


class SQLiteTransport(AbstractTransport):
    _name = "SQLite"
    _base_path: str = None
    _root_path: str = None
    _is_writing: bool = False
    _scheduler = sched.scheduler(time.time, time.sleep)
    _polling_interval = 0.5  # seconds
    __connection: sqlite3.Connection = None
    app_name: str = ""
    scope: str = ""
    saved_obj_count: int = 0

    def __init__(
        self,
        base_path: str = None,
        app_name: str = None,
        scope: str = None,
        **data: Any,
    ) -> None:
        super().__init__(**data)
        self.app_name = app_name or "Speckle"
        self.scope = scope or "Objects"
        self._base_path = base_path or self.__get_base_path()

        try:
            os.makedirs(self._base_path, exist_ok=True)

            self._root_path = os.path.join(
                os.path.join(self._base_path, f"{self.scope}.db")
            )
            self.__initialise()
        except Exception as ex:
            raise SpeckleException(
                f"SQLiteTransport could not initialise {self.scope}.db at {self._base_path}. Either provide a different `base_path` or use an alternative transport.",
                ex,
            )

    def __repr__(self) -> str:
        return f"SQLiteTransport(app: '{self.app_name}', scope: '{self.scope}')"

    # def __write_timer_elapsed(self):
    #     print("WRITE TIMER ELAPSED")
    #     proc = Process(target=_run_queue, args=(self.__queue, self._root_path))
    #     proc.start()
    #     proc.join()

    def __get_base_path(self):
        # from appdirs https://github.com/ActiveState/appdirs/blob/master/appdirs.py
        # default mac path is not the one we use (we use unix path), so using special case for this
        system = sys.platform
        if system.startswith("java"):
            import platform

            os_name = platform.java_ver()[3][0]
            if os_name.startswith("Mac"):
                system = "darwin"

        if system != "darwin":
            return user_data_dir(appname=self.app_name, appauthor=False, roaming=True)

        path = os.path.expanduser("~/.config/")
        return os.path.join(path, self.app_name)

    # def __consume_queue(self):
    #     if self._is_writing or self.__queue.empty():
    #         return
    #     print("CONSUME QUEUE")
    #     self._is_writing = True
    #     while not self.__queue.empty():
    #         data = self.__queue.get()
    #         self.save_object(data[0], data[1])
    #     self._is_writing = False

    #     self._scheduler.enter(
    #         delay=self._polling_interval, priority=1, action=self.__consume_queue
    #     )
    #     self._scheduler.run(blocking=True)

    # def save_object(self, id: str, serialized_object: str) -> None:
    #     """Adds an object to the queue and schedules it to be saved.

    #     Arguments:
    #         id {str} -- the object id
    #         serialized_object {str} -- the full string representation of the object
    #     """
    #     print("SAVE OBJECT")
    #     self.__queue.put((id, serialized_object))

    #     self._scheduler.enter(
    #         delay=self._polling_interval, priority=1, action=self.__consume_queue
    #     )
    #     self._scheduler.run(blocking=True)

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        """Adds an object from the given transport to the the local db

        Arguments:
            id {str} -- the object id
            source_transport {AbstractTransport) -- the transport through which the object can be found
        """
        serialized_object = source_transport.get_object(id)
        self.save_object(id, serialized_object)

    def save_object(self, id: str, serialized_object: str) -> None:
        """Directly saves an object into the database.

        Arguments:
            id {str} -- the object id
            serialized_object {str} -- the full string representation of the object
        """
        self.__check_connection()
        try:
            with closing(self.__connection.cursor()) as c:
                c.execute(
                    "INSERT OR IGNORE INTO objects(hash, content) VALUES(?,?)",
                    (id, serialized_object),
                )
                self.__connection.commit()
        except Exception as ex:
            raise SpeckleException(
                f"Could not save the object to the local db. Inner exception: {ex}", ex
            )

    def get_object(self, id: str) -> str or None:
        self.__check_connection()
        with closing(self.__connection.cursor()) as c:
            row = c.execute(
                "SELECT * FROM objects WHERE hash = ? LIMIT 1", (id,)
            ).fetchone()
        return row[1] if row else None

    def has_objects(self, id_list: List[str]) -> Dict[str, bool]:
        ret = {}
        self.__check_connection()
        with closing(self.__connection.cursor()) as c:
            for id in id_list:
                row = c.execute(
                    "SELECT 1 FROM objects WHERE hash = ? LIMIT 1", (id,)
                ).fetchone()
                ret[id] = bool(row)
        return ret

    def begin_write(self):
        self.saved_obj_count = 0

    def end_write(self):
        pass

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        raise NotImplementedError

    def get_all_objects(self):
        """Returns all the objects in the store. NOTE: do not use for large collections!"""
        self.__check_connection()
        with closing(self.__connection.cursor()) as c:
            rows = c.execute("SELECT * FROM objects").fetchall()
        return rows

    def close(self):
        """Close the connection to the database"""
        if self.__connection:
            self.__connection.close()
            self.__connection = None

    def __initialise(self) -> None:
        self.__connection = sqlite3.connect(self._root_path)
        with closing(self.__connection.cursor()) as c:
            c.execute(
                """ CREATE TABLE IF NOT EXISTS objects(
                      hash TEXT PRIMARY KEY,
                      content TEXT
                    ) WITHOUT ROWID;"""
            )
            c.execute("PRAGMA journal_mode='wal';")
            c.execute("PRAGMA count_changes=OFF;")
            c.execute("PRAGMA temp_store=MEMORY;")
            self.__connection.commit()

    def __check_connection(self):
        if not self.__connection:
            self.__connection = sqlite3.connect(self._root_path)

    def __del__(self):
        self.__connection.close()


# def _run_queue(queue: Queue, root_path: str):
#     if queue.empty():
#         return
#     print("RUN QUEUE")
#     conn = sqlite3.connect(root_path)
#     while not queue.empty():
#         data = queue.get()
#         with closing(conn.cursor()) as c:
#             c.execute(
#                 "INSERT OR IGNORE INTO objects(hash, content) VALUES(?,?)",
#                 (data[0], data[1]),
#             )
#             conn.commit()
#     conn.close()
