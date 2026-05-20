import pytest
import sqlite3
from datetime import datetime
from timetracker.db.connection import init_db
from timetracker.services.sessions import SessionService


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    conn.execute(
        "INSERT INTO goals (title, description, target_hours, color) VALUES ('G','',10,'#fff')"
    )
    conn.commit()
    yield conn
    conn.close()


def test_start_session_creates_db_record(db):
    svc = SessionService(db)
    session_id = svc.start(
        goal_id=1, intent="Write code", pomodoro_number=1,
        planned_duration=25, started_at=datetime(2026, 5, 19, 9, 0),
    )
    assert session_id > 0
    row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    assert row["intent"] == "Write code"


def test_complete_session(db):
    svc = SessionService(db)
    sid = svc.start(goal_id=1, intent="x", pomodoro_number=1,
                    planned_duration=25, started_at=datetime(2026, 5, 19, 9, 0))
    svc.complete(session_id=sid, ended_at=datetime(2026, 5, 19, 9, 25),
                 actual_duration=25, reflection="Done well", focus_score=5)
    row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    assert row["completed"] == 1
    assert row["focus_score"] == 5


def test_today_summary(db):
    svc = SessionService(db)
    sid = svc.start(goal_id=1, intent="x", pomodoro_number=1,
                    planned_duration=25, started_at=datetime.now())
    svc.complete(session_id=sid, ended_at=datetime.now(),
                 actual_duration=25, reflection="ok", focus_score=3)
    summary = svc.today_summary()
    assert summary["completed_pomodoros"] == 1
    assert summary["total_minutes"] == 25


def test_recent_focus_scores(db):
    svc = SessionService(db)
    for score in [3, 4, 5]:
        sid = svc.start(goal_id=1, intent="x", pomodoro_number=1,
                        planned_duration=25, started_at=datetime(2026, 5, 19, 9, 0))
        svc.complete(session_id=sid, ended_at=datetime(2026, 5, 19, 9, 25),
                     actual_duration=25, reflection="ok", focus_score=score)
    scores = svc.recent_focus_scores(limit=3)
    assert len(scores) == 3


def test_streak(db):
    svc = SessionService(db)
    sid = svc.start(goal_id=1, intent="x", pomodoro_number=1,
                    planned_duration=25, started_at=datetime.now())
    svc.complete(session_id=sid, ended_at=datetime.now(),
                 actual_duration=25, reflection="ok", focus_score=4)
    assert svc.streak() >= 1
