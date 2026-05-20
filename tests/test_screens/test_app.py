import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


async def test_app_launches_and_shows_dashboard():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        with patch("timetracker.db.connection.create_connection") as mock_conn:
            import sqlite3
            from timetracker.db.connection import init_db
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            init_db(conn)
            mock_conn.return_value = conn

            from timetracker.main import TimeTrackerApp
            app = TimeTrackerApp()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause(0.1)
                assert app.screen is not None
