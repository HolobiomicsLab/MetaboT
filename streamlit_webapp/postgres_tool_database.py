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

    def initialize_db(self):
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
        """
        Fetch the most recent value for <tool_name>_data.
        • If the latest interaction has a non-NULL value, return it.
        • Otherwise, fall back to the previous interaction (if any).
        • Return None when no data is found.
        """
        session_id = get_session_id()
        thread_id = get_thread_id()

        with self.conn, self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                # Grab the two most-recent interactions for this session/thread
                cursor.execute(
                    f"""
                    SELECT interaction, {tool_name}_data
                    FROM tool_data
                    WHERE session_id = %s AND thread_id = %s
                    ORDER BY interaction DESC
                    LIMIT 2;
                    """,
                    (session_id, thread_id),
                )
                rows = cursor.fetchall()

                if not rows:  # ─── Case 0: no interactions at all
                    logger.info("No interactions found for tool '%s'.", tool_name)
                    return None

                latest_interaction = rows[0]["interaction"]
                latest_data = rows[0][f"{tool_name}_data"]

                if latest_data is not None:  # ─── Case 1
                    logger.info(
                        "Data found for tool '%s' in latest interaction (%s).",
                        tool_name,
                        latest_interaction,
                    )
                    return latest_data

                # ─── Case 2: latest data is NULL – fall back to previous row if it exists
                logger.info(
                    "Data for tool '%s' is NULL in latest interaction (%s). "
                    "Checking previous.",
                    tool_name,
                    latest_interaction,
                )

                if len(rows) > 1:  # previous interaction exists
                    prev_interaction = rows[1]["interaction"]
                    prev_data = rows[1][f"{tool_name}_data"]
                    logger.info(
                        "Returning data for tool '%s' from previous interaction (%s).",
                        tool_name,
                        prev_interaction,
                    )
                    return prev_data

                # ─── Case 3: only one interaction and it's NULL
                logger.info(
                    "No previous interaction found or data is NULL for tool '%s'.",
                    tool_name,
                )
                return None

            except Exception as e:
                logger.error(
                    "Database error retrieving data for tool '%s': %s", tool_name, e
                )
                return None