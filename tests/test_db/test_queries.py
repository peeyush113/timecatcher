import pytest
from datetime import datetime
from timetracker.db import queries


def test_create_and_get_goal(db):
    goal_id = queries.create_goal(db, title="Write thesis", description="PhD work",
                                   target_hours=100.0, color="#4CAF50")
    goal = queries.get_goal(db, goal_id)
    assert goal["title"] == "Write thesis"
    assert goal["target_hours"] == 100.0
    assert goal["archived"] == 0


def test_list_goals_excludes_archived(db):
    queries.create_goal(db, title="Active", description="", target_hours=10, color="#fff")
    aid = queries.create_goal(db, title="Old", description="", target_hours=5, color="#aaa")
    queries.archive_goal(db, aid)
    goals = queries.list_goals(db)
    assert len(goals) == 1
    assert goals[0]["title"] == "Active"


def test_create_session_and_retrieve(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    sid = queries.create_session(
        db, goal_id=gid, started_at=datetime(2026, 5, 19, 9, 0),
        planned_duration=25, session_type="work", pomodoro_number=1,
        intent="Write intro",
    )
    session = queries.get_session(db, sid)
    assert session["intent"] == "Write intro"
    assert session["completed"] == 0


def test_complete_session(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    sid = queries.create_session(
        db, goal_id=gid, started_at=datetime(2026, 5, 19, 9, 0),
        planned_duration=25, session_type="work", pomodoro_number=1, intent="x",
    )
    queries.complete_session(
        db, session_id=sid, ended_at=datetime(2026, 5, 19, 9, 25),
        actual_duration=25, reflection="Done", focus_score=4,
    )
    session = queries.get_session(db, sid)
    assert session["completed"] == 1
    assert session["focus_score"] == 4
    assert session["reflection"] == "Done"


def test_total_hours_for_goal(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    s2 = queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 19, 10, 0),
                                 planned_duration=25, session_type="work", pomodoro_number=1, intent="y")
    queries.complete_session(db, session_id=s2, ended_at=datetime(2026, 5, 19, 10, 25),
                              actual_duration=25, reflection="r", focus_score=5)
    hours = queries.total_hours_for_goal(db, gid)
    assert hours == pytest.approx(25 / 60)


def test_sessions_today(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 19, 8, 0),
                            planned_duration=25, session_type="work", pomodoro_number=1, intent="a")
    queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 18, 8, 0),
                            planned_duration=25, session_type="work", pomodoro_number=1, intent="b")
    today = queries.sessions_today(db, date="2026-05-19")
    assert len(today) == 1


def test_recent_focus_scores(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    for score in [3, 4, 5]:
        sid = queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 19, 9, 0),
                                      planned_duration=25, session_type="work", pomodoro_number=1, intent="x")
        queries.complete_session(db, session_id=sid, ended_at=datetime(2026, 5, 19, 9, 25),
                                  actual_duration=25, reflection="ok", focus_score=score)
    scores = queries.recent_focus_scores(db, limit=3)
    assert scores == [3, 4, 5]


def test_current_streak_single_day(db):
    gid = queries.create_goal(db, title="G", description="", target_hours=10, color="#fff")
    from datetime import date
    today = date.today().isoformat() + "T09:00:00"
    sid = queries.create_session(db, goal_id=gid, started_at=today,
                                  planned_duration=25, session_type="work", pomodoro_number=1, intent="x")
    queries.complete_session(db, session_id=sid, ended_at=today,
                              actual_duration=25, reflection="ok", focus_score=4)
    assert queries.current_streak(db) == 1
