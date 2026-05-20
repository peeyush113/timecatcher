import pytest
import sqlite3
from timetracker.db.connection import init_db
from timetracker.services.goals import GoalService
from timetracker.models import Goal


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    yield conn
    conn.close()


def test_create_goal_returns_goal_object(db):
    svc = GoalService(db)
    goal = svc.create("Learn Rust", description="Systems programming", target_hours=50)
    assert isinstance(goal, Goal)
    assert goal.title == "Learn Rust"
    assert goal.id > 0


def test_list_active_goals(db):
    svc = GoalService(db)
    svc.create("G1", target_hours=10)
    svc.create("G2", target_hours=20)
    goals = svc.list_active()
    assert len(goals) == 2


def test_progress_zero_when_no_sessions(db):
    svc = GoalService(db)
    goal = svc.create("G", target_hours=10)
    assert svc.progress_pct(goal.id) == 0.0


def test_progress_pct(db):
    svc = GoalService(db)
    goal = svc.create("G", target_hours=10)
    # 300 minutes = 5 hours = 50% of 10h target
    db.execute(
        "INSERT INTO sessions (goal_id, started_at, planned_duration, session_type, "
        "pomodoro_number, actual_duration, completed) VALUES (?,?,?,?,?,?,1)",
        (goal.id, "2026-05-19T09:00:00", 25, "work", 1, 300),
    )
    db.commit()
    assert svc.progress_pct(goal.id) == pytest.approx(50.0)


def test_progress_capped_at_100(db):
    svc = GoalService(db)
    goal = svc.create("G", target_hours=1)
    db.execute(
        "INSERT INTO sessions (goal_id, started_at, planned_duration, session_type, "
        "pomodoro_number, actual_duration, completed) VALUES (?,?,?,?,?,?,1)",
        (goal.id, "2026-05-19T09:00:00", 25, "work", 1, 1000),
    )
    db.commit()
    assert svc.progress_pct(goal.id) == 100.0


def test_archive_goal(db):
    svc = GoalService(db)
    goal = svc.create("G", target_hours=10)
    svc.archive(goal.id)
    assert len(svc.list_active()) == 0
