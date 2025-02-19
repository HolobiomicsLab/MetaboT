import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError
from app.core.memory.tools_database import ToolsDatabaseManager
from app.core.session import setup_logger, get_session_id, get_thread_id
import sys
from pathlib import Path
from datetime import datetime
import os

logger = setup_logger(__name__)

class PostgresToolsDatabaseManager(ToolsDatabaseManager):
    db_url = os.environ.get("DATABASE_URL")

    def __init__(self):
        self.db_url = self.db_url
        self.conn = None
        self.connect_db()

    def connect_db(self):
        try:
            if self.conn is None or self.conn.closed != 0:
                self.conn = psycopg2.connect(self.db_url)
        except Exception as e:
            print("Unable to connect to the database:", e)
            raise e

    def add_interaction(self):
        session_id = get_session_id()
        thread_id = get_thread_id()
        current_utc_time = datetime.utcnow()

        with self.conn, self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT MAX(interaction) as max_interaction
                FROM tool_data
                WHERE session_id = %s AND thread_id = %s;
            """, (session_id, thread_id))
            result = cursor.fetchone()
            max_interaction = result['max_interaction'] if result and result['max_interaction'] is not None else 0

            new_interaction = max_interaction + 1
            cursor.execute("""
                INSERT INTO tool_data (session_id, thread_id, interaction, timestamp)
                VALUES (%s, %s, %s, %s);
            """, (session_id, thread_id, new_interaction, current_utc_time))

    def put(self, data, tool_name):
        session_id = get_session_id()
        thread_id = get_thread_id()
        current_utc_time = datetime.utcnow()

        with self.conn, self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"""
                UPDATE tool_data
                SET {tool_name}_data = %s, timestamp = %s
                WHERE session_id = %s AND thread_id = %s AND interaction = (
                    SELECT MAX(interaction) FROM tool_data WHERE session_id = %s AND thread_id = %s
                );
            """, (data, current_utc_time, session_id, thread_id, session_id, thread_id))

    def get(self, tool_name):
        session_id = get_session_id()
        thread_id = get_thread_id()

        with self.conn, self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"""
                SELECT {tool_name}_data
                FROM tool_data
                WHERE session_id = %s AND thread_id = %s
                ORDER BY interaction DESC
                LIMIT 1;
            """, (session_id, thread_id))
            result = cursor.fetchone()
            return result.get(f"{tool_name}_data") if result else None