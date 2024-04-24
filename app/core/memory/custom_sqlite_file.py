# This is a custom sqlite checkpoint for langgraph based on the orininal one https://github.com/langchain-ai/langgraph/blob/main/langgraph/checkpoint/sqlite.py commit @f2ad930 https://github.com/langchain-ai/langgraph/commit/f2ad930cd4cf383ccaefd18d497aa2e0f459e5bd
# This custom sqlite allows multithreading access, necessary for running the langgraph with memory in Streamlit.

import os
import pickle
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

from langchain_core.pydantic_v1 import Field
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import ConfigurableFieldSpec
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint

from app.core.utils import setup_logger

logger = setup_logger(__name__)


class SqliteSaver(BaseCheckpointSaver):
    # Specify the path to the database file
    database_path = "langgraph_checkpoint.db"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Ensure proper Pydantic initialization
        self.__dict__["_local"] = threading.local()
        self._initialize_database()

    def _initialize_database(self):
        # Check if the database file exists and delete it if so
        if os.path.exists(self.database_path):
            os.remove(self.database_path)
        # Establish a new database connection to the file
        self._get_connection(force_new=True)

    def _get_connection(self, force_new=False):
        if not hasattr(self._local, "connection") or force_new:
            self._local.connection = sqlite3.connect(
                self.database_path, check_same_thread=False
            )
        else:
            pass
        return self._local.connection

    def setup(self):
        if hasattr(self._local, "is_setup") and self._local.is_setup:
            return

        conn = self._get_connection()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT PRIMARY KEY,
                checkpoint BLOB
            );
        """
        )
        self._local.is_setup = True

    @contextmanager
    def cursor(self, transaction: bool = True):
        self.setup()
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            yield cur
        finally:
            if transaction:
                conn.commit()
            cur.close()

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        with self.cursor(transaction=False) as cur:
            cur.execute(
                "SELECT checkpoint FROM checkpoints WHERE thread_id = ?",
                (config["configurable"]["thread_id"],),
            )
            row = cur.fetchone()
            return pickle.loads(row[0]) if row else None

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        with self.cursor() as cur:
            cur.execute(
                "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint) VALUES (?, ?)",
                (config["configurable"]["thread_id"], pickle.dumps(checkpoint)),
            )

    # For debugging
    def print_database_contents(self):
        with self.cursor(transaction=False) as cur:
            cur.execute("SELECT thread_id, checkpoint FROM checkpoints")
            rows = cur.fetchall()
            for row in rows:
                print(
                    f"Thread ID: {row[0]}, Checkpoint (Raw): {row[1][:100]}..."
                )  # Print a portion of the checkpoint to avoid flooding the output
