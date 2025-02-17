import os
import threading
import pickle
import psycopg2
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional

from langchain_core.pydantic_v1 import Field
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import ConfigurableFieldSpec
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint

class PostgresCheckpointerSaver(BaseCheckpointSaver):
    connection_string: str = os.environ.get("DATABASE_URL")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__['_local'] = threading.local()
        self._initialize_database()

    def _initialize_database(self):
        # Establish a new database connection to PostgreSQL
        self._get_connection(force_new=True)
        self.setup()

    def _get_connection(self, force_new=False):
        if not hasattr(self._local, 'connection') or force_new:
            self._local.connection = psycopg2.connect(self.connection_string)
        return self._local.connection

    def setup(self):
        if hasattr(self._local, 'is_setup') and self._local.is_setup:
            return

        conn = self._get_connection()
        with conn.cursor() as cur:
            # Ensure the database uses UTC
            cur.execute("SET timezone='UTC';")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    checkpoint BYTEA,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        self._local.is_setup = True

    @contextmanager
    def cursor(self, transaction: bool = True):
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
            cur.execute("SELECT checkpoint FROM checkpoints WHERE thread_id = %s", (config["configurable"]["thread_id"],))
            row = cur.fetchone()
            return pickle.loads(row[0]) if row else None

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        with self.cursor() as cur:
            # Ensure the timestamp is in UTC
            utc_timestamp = datetime.now(timezone.utc)
            cur.execute("""
                INSERT INTO checkpoints (thread_id, checkpoint, created_at) 
                VALUES (%s, %s, %s)
                ON CONFLICT (thread_id) 
                DO UPDATE SET checkpoint = EXCLUDED.checkpoint, created_at = CURRENT_TIMESTAMP
            """, (config["configurable"]["thread_id"], pickle.dumps(checkpoint), utc_timestamp))

    # For debugging
    def print_database_contents(self):
        with self.cursor(transaction=False) as cur:
            cur.execute("SELECT thread_id, checkpoint FROM checkpoints")
            rows = cur.fetchall()
            for row in rows:
                print(f"Thread ID: {row[0]}, Checkpoint (Raw): {row[1][:100]}...")  # Print a portion of the checkpoint to avoid flooding the output

    def test_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            print("Connected successfully!")
        except Exception as e:
            print("Failed to connect:", e)
        finally:
            if conn:
                conn.close()