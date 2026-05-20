import sqlite3
from pathlib import Path
import tempfile
from timetracker.db.connection import create_connection, init_db, DEFAULT_SETTINGS


def test_init_db_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert {"goals", "tasks", "sessions", "settings"} <= tables


def test_init_db_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        init_db(conn)  # should not raise
        count = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        assert count == len(DEFAULT_SETTINGS)


def test_default_settings_inserted():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'work_duration'"
        ).fetchone()
        assert row is not None
        assert row[0] == "25"


def test_foreign_keys_enforced():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        try:
            conn.execute(
                "INSERT INTO tasks (goal_id, title) VALUES (999, 'orphan')"
            )
            conn.commit()
            assert False, "Should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass
