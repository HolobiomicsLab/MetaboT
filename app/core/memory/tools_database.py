import sqlite3
from pathlib import Path
from ..session import setup_logger, get_session_id
from abc import ABC, abstractmethod
import os
import sys

logger = setup_logger(__name__)

class ToolsDatabaseManager(ABC):
    @abstractmethod
    def add_interaction(self):
        """Add a new interaction or increment the interaction counter."""
        pass

    @abstractmethod
    def put(self, tool_name, data):
        """Insert or update data associated with a tool at the current interaction."""
        pass

    @abstractmethod
    def get(self, tool_name):
        """Retrieve the most recent data for the specified tool."""
        pass

class SqliteToolsDatabaseManager(ToolsDatabaseManager):
    _instance = None

    def __new__(cls, db_path='tools_database.db', reset=False):
        """
        Singleton pattern with optional reset capability.
        """ 
        if cls._instance is None or reset:
            cls._instance = super(SqliteToolsDatabaseManager, cls).__new__(cls)
            cls._instance.init(db_path)
        return cls._instance

    def init(self, db_path):
        """
        Initialize the database manager with the given database path.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.initialize_db()
        logger.info(f"SqliteToolsDatabase initialized with path: {self.db_path}")

    def initialize_db(self):
        """
        Initialize the database with necessary tables and columns.
        """
        # Assuming tools are known and fixed for simplicity.
        tools_columns = self.discover_tool_columns()
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    interaction INTEGER PRIMARY KEY AUTOINCREMENT,
                    {tool_columns}
                );
            """.format(tool_columns=', '.join([f"{tool}_data TEXT DEFAULT NULL" for tool in tools_columns])))
            conn.commit()
            session_id = get_session_id()
            logger.info(f"Database initialized with {tools_columns}_data columns. Session_id = {session_id}")

    def discover_tool_columns(self):
        """
        Discover available tool columns by iterating over each subdirectory in 'app/core/agents'
        and using the import_tools function to load tools from each agent module.
        """
        agents_folder = Path(__file__).resolve().parent.parent / "agents"
        tool_names = []


        for root, dirs, files in os.walk(agents_folder):
            for filename in files:

                if filename.startswith("tool_") and filename.endswith(".py"):
                    tool_names.append(filename[:-3])  # Remove ".py" from the filename

        return tool_names

    def add_interaction(self):
        """
        Add a new row to increment the interaction counter.
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metadata DEFAULT VALUES;
            """)
            conn.commit()
        logger.info("Interaction added.")

    def put(self, data, tool_name):
        """
        Update the existing row at the highest interaction count with new data.
        """

        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE metadata
                SET {tool_name}_data = ?
                WHERE interaction = (SELECT MAX(interaction) FROM metadata)
            """, (data,))
            conn.commit()
        logger.info(f"Data for {tool_name} updated.")

    def get(self, filename):
        """
        Select the most recent data for the given filename (tool).
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {filename}_data FROM metadata
                ORDER BY interaction DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            logger.info(f"Data for {filename} retrieved.")
            return result[0] if result else None
        