import time
import os
import sqlite3
import requests


class HTTPCache:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, "cache.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create cache table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

    def get(self, url):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT content, fetched_at FROM cache 
                WHERE url = ?
                ORDER BY fetched_at DESC
                LIMIT 1
            """,
                (url,),
            )
            row = cursor.fetchone()

            if row:
                return row[0]
            return None

    def put(self, url, content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (url, content, fetched_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (url, content),
            )
            conn.commit()

    def fetch(self, url, headers=None, timeout=1):
        # check catch then fetch if not in cache
        cached = self.get(url)
        if cached:
            return cached

        response = requests.get(url, headers=headers or {}, timeout=timeout)
        # Rate limit
        time.sleep(0.1)
        response.raise_for_status()

        content = response.text
        self.put(url, content)

        return content
