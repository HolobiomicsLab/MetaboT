import os
from app.core.memory.tools_database import SqliteToolsDatabaseManager
from app.core.memory.custom_sqlite_file import SqliteCheckpointerSaver
import importlib

def tools_database():
    """
    Get the database manager based on the environment variables

    :return: The database manager
    """
    if os.getenv('DATABASE_URL') and os.getenv("TOOLS_DATABASE_MANAGER_CLASS"):
        class_path = os.getenv('TOOLS_DATABASE_MANAGER_CLASS')
        if class_path:
            # Dynamically import the module and class based on the environment variable
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            manager_class = getattr(module, class_name)
            return manager_class()
    else:
        return SqliteToolsDatabaseManager()

def memory_database():
    """
    Get the database manager based on the environment variables

    :return: The database manager
    """

    if os.getenv('DATABASE_URL') and os.getenv("MEMORY_DATABASE_MANAGER_CLASS"):
        class_path = os.getenv('MEMORY_DATABASE_MANAGER_CLASS')
        if class_path:
            # Dynamically import the module and class based on the environment variable
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            manager_class = getattr(module, class_name)
            return manager_class()
    else:
        return SqliteCheckpointerSaver()