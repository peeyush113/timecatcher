from timetracker.models import Goal, Task, Session, TimerStatus, SessionType
from datetime import datetime


def test_goal_fields():
    g = Goal(id=1, title="Write thesis", description="PhD", target_hours=100.0,
              color="#4CAF50", created_at=datetime(2026, 1, 1))
    assert g.title == "Write thesis"
    assert g.archived is False


def test_session_defaults():
    s = Session(
        id=1, goal_id=1, started_at=datetime(2026, 1, 1),
        planned_duration=25, session_type=SessionType.WORK, pomodoro_number=1,
    )
    assert s.completed is False
    assert s.focus_score is None
    assert s.intent is None


def test_timer_status_idle_is_default():
    assert TimerStatus.IDLE.name == "IDLE"


def test_session_type_values():
    assert SessionType.WORK.value == "work"
    assert SessionType.SHORT_BREAK.value == "short_break"
    assert SessionType.LONG_BREAK.value == "long_break"
