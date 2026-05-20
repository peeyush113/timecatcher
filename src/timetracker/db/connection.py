import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    target_hours REAL DEFAULT 0,
    color TEXT DEFAULT '#4CAF50',
    created_at TEXT DEFAULT (datetime('now')),
    archived INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id),
    task_id INTEGER REFERENCES tasks(id),
    intent TEXT,
    reflection TEXT,
    focus_score INTEGER CHECK (focus_score IS NULL OR (focus_score BETWEEN 1 AND 5)),
    planned_duration INTEGER NOT NULL DEFAULT 25,
    actual_duration INTEGER,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    completed INTEGER DEFAULT 0,
    session_type TEXT NOT NULL DEFAULT 'work',
    pomodoro_number INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS: dict[str, str] = {
    "work_duration": "25",
    "short_break_duration": "5",
    "long_break_duration": "15",
    "pomodoros_per_set": "4",
}


def create_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    if db_path is None:
        data_dir = Path.home() / ".timetracker"
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / "data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
