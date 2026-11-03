"""Singleton database connection (SQLite)."""
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL CHECK (kind IN ('printed', 'ebook', 'audiobook')),
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  isbn TEXT NOT NULL UNIQUE,
  extra TEXT NOT NULL DEFAULT '',        -- pages / file size MB / duration min, by kind
  copies INTEGER NOT NULL CHECK (copies >= 0),
  available INTEGER NOT NULL CHECK (available >= 0 AND available <= copies)
);
CREATE TABLE IF NOT EXISTS members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
  member_id INTEGER NOT NULL REFERENCES members(id),
  returned INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS waitlist (
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  member_id INTEGER NOT NULL REFERENCES members(id),
  PRIMARY KEY (book_id, member_id)
);
"""


class Database:
    """One shared connection per process. Database() always returns the same object;
    the path given on first use wins, and later calls with a different path raise."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, path="library.db"):
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst.path = path
                inst.conn = sqlite3.connect(path, check_same_thread=False)
                inst.conn.row_factory = sqlite3.Row
                inst.conn.execute("PRAGMA foreign_keys = ON")
                inst.conn.executescript(SCHEMA)
                cls._instance = inst
            elif path != cls._instance.path:
                raise RuntimeError(f"Database already open at {cls._instance.path!r}")
            return cls._instance

    @classmethod
    def close(cls):
        with cls._lock:
            if cls._instance is not None:
                cls._instance.conn.close()
                cls._instance = None

    def execute(self, sql, params=()):
        with self.conn:  # commit on success, roll back on error
            return self.conn.execute(sql, params)

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()
