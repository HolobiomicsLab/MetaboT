from pathlib import Path
import datetime
import tempfile

def cleanup_old_files(directory_path):
    # Get the current time in UTC
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Define the age limit for files (1 hour)
    age_limit = datetime.timedelta(hours=1)
    
    # Create a Path object for the directory
    directory = Path(directory_path)
    
    # Check if the directory exists
    if not directory.exists():
        print(f"The directory {directory} does not exist.")
        return
    
    # Check each file and subdirectory in the specified directory
    for file_path in directory.iterdir():
        if file_path.is_file():
            # Get the file's modification time in UTC
            file_mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime, datetime.timezone.utc)
            file_age = now - file_mod_time
            
            # If the file is older than 1 hour, delete it
            if file_age > age_limit:
                file_path.unlink()
                print(f"Deleted {file_path} - Age: {file_age}")
        elif file_path.is_dir():
            # Recursively delete files inside directories
            cleanup_old_files(file_path)
            # If the directory is empty, remove it
            if not any(file_path.iterdir()):
                file_path.rmdir()
                print(f"Deleted empty directory: {file_path}")

if __name__ == "__main__":
    # Modify this to clean up two specific directories
    kgbot_tempdir = Path(tempfile.gettempdir()) / "kgbot"
    directories = ['./.codebox', kgbot_tempdir]
    for directory in directories:
        cleanup_old_files(directory)