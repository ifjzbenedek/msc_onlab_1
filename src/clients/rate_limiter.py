import os
import sqlite3
import time


class RateLimiter:

    def __init__(self, db_path: str, interval_seconds: float) -> None:
        self.db_path = db_path
        self.interval = interval_seconds

        folder = os.path.dirname(db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS rate_limit (id INTEGER PRIMARY KEY, last_at REAL)"
        )
        conn.execute("INSERT OR IGNORE INTO rate_limit (id, last_at) VALUES (1, 0)")
        conn.commit()
        conn.close()

    def acquire(self) -> None:
        while True:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT last_at FROM rate_limit WHERE id=1").fetchone()
            last = row[0] if row else 0.0
            now = time.time()
            wait = (last + self.interval) - now

            if wait <= 0:
                conn.execute("UPDATE rate_limit SET last_at=? WHERE id=1", (now,))
                conn.commit()
                conn.close()
                return

            conn.close()
            time.sleep(wait)
