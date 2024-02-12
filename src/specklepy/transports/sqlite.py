import os
import sqlite3
from contextlib import closing
from typing import Dict, List, Optional, Tuple

from specklepy.core.helpers import speckle_path_provider
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.abstract_transport import AbstractTransport


class SQLiteTransport(AbstractTransport):
    def __init__(
        self,
        base_path: Optional[str] = None,
        app_name: Optional[str] = None,
        scope: Optional[str] = None,
        max_batch_size_mb: float = 10.0,
        name: str = "SQLite",
    ) -> None:
        super().__init__()
        self._name = name
        self.app_name = app_name or "Speckle"
        self.scope = scope or "Objects"
        self._base_path = base_path or self.get_base_path(self.app_name)
        self.max_size = int(max_batch_size_mb * 1000 * 1000)
        self.saved_obj_count = 0
        self._current_batch: List[Tuple[str, str]] = []
        self._current_batch_size = 0

        try:
            os.makedirs(self._base_path, exist_ok=True)

            self._root_path = os.path.join(
                os.path.join(self._base_path, f"{self.scope}.db")
            )
            self.__initialise()
        except Exception as ex:
            raise SpeckleException(
                f"SQLiteTransport could not initialise {self.scope}.db at"
                f" {self._base_path}. Either provide a different `base_path` or use an"
                " alternative transport.",
                ex,
            )

    def __repr__(self) -> str:
        return f"SQLiteTransport(app: '{self.app_name}', scope: '{self.scope}')"

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def get_base_path(app_name):
        return str(
            speckle_path_provider.user_application_data_path().joinpath(app_name)
        )

    def save_object_from_transport(
        self, id: str, source_transport: AbstractTransport
    ) -> None:
        """Adds an object from the given transport to the the local db

        Arguments:
            id {str} -- the object id
            source_transport {AbstractTransport)
            -- the transport through which the object can be found
        """
        serialized_object = source_transport.get_object(id)
        self.save_object(id, serialized_object)

    def save_object(self, id: str, serialized_object: str) -> None:
        """
        Adds an object to the current batch to be written to the db.
        If the current batch is full,
        the batch is written to the db and the current batch is reset.

        Arguments:
            id {str} -- the object id
            serialized_object {str} -- the full string representation of the object
        """
        obj_size = len(serialized_object)
        if (
            not self._current_batch
            or self._current_batch_size + obj_size < self.max_size
        ):
            self._current_batch.append((id, serialized_object))
            self._current_batch_size += obj_size
            return

        self.save_current_batch()
        self._current_batch = [(id, serialized_object)]
        self._current_batch_size = obj_size

    def save_current_batch(self) -> None:
        """Save the current batch of objects to the local db"""
        self.__check_connection()
        try:
            with closing(self.__connection.cursor()) as c:
                c.executemany(
                    "INSERT OR IGNORE INTO objects(hash, content) VALUES(?,?)",
                    self._current_batch,
                )
                self.__connection.commit()
        except Exception as ex:
            raise SpeckleException(
                "Could not save the batch of objects to the local db. Inner exception:"
                f" {ex}",
                ex,
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
        self._object_cache = []
        self.saved_obj_count = 0

    def end_write(self):
        if self._current_batch:
            self.save_current_batch()
        self._current_batch = []
        self._current_batch_size = 0

    def copy_object_and_children(
        self, id: str, target_transport: AbstractTransport
    ) -> str:
        raise NotImplementedError

    def get_all_objects(self):
        """
        Returns all the objects in the store.
        NOTE: do not use for large collections!
        """
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
        self.close()
