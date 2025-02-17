import os
import psycopg2
from datetime import datetime, timedelta, timezone

def clean_database():
    connection_string = os.environ.get("DATABASE_URL")
    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

            # Execute the DELETE command
            cur.execute("DELETE FROM checkpoints WHERE created_at < %s", (cutoff_time,))
            conn.commit()
            print(f"Deleted checkpoints older than: {cutoff_time.isoformat()}")

if __name__ == "__main__":
    clean_database()