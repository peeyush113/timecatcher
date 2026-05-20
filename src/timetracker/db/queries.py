import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional


def create_goal(conn: sqlite3.Connection, title: str, description: str,
                target_hours: float, color: str) -> int:
    cur = conn.execute(
        "INSERT INTO goals (title, description, target_hours, color) VALUES (?, ?, ?, ?)",
        (title, description, target_hours, color),
    )
    conn.commit()
    return cur.lastrowid


def get_goal(conn: sqlite3.Connection, goal_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()


def list_goals(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM goals WHERE archived = 0 ORDER BY created_at"
    ).fetchall()


def archive_goal(conn: sqlite3.Connection, goal_id: int) -> None:
    conn.execute("UPDATE goals SET archived = 1 WHERE id = ?", (goal_id,))
    conn.commit()


def update_goal(conn: sqlite3.Connection, goal_id: int, title: str,
                description: str, target_hours: float, color: str) -> None:
    conn.execute(
        "UPDATE goals SET title=?, description=?, target_hours=?, color=? WHERE id=?",
        (title, description, target_hours, color, goal_id),
    )
    conn.commit()


def create_session(conn: sqlite3.Connection, goal_id: int, started_at,
                   planned_duration: int, session_type: str, pomodoro_number: int,
                   intent: Optional[str] = None, task_id: Optional[int] = None) -> int:
    if isinstance(started_at, datetime):
        started_at = started_at.isoformat()
    cur = conn.execute(
        """INSERT INTO sessions
           (goal_id, task_id, intent, planned_duration, started_at, session_type, pomodoro_number)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (goal_id, task_id, intent, planned_duration, started_at, session_type, pomodoro_number),
    )
    conn.commit()
    return cur.lastrowid


def get_session(conn: sqlite3.Connection, session_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()


def complete_session(conn: sqlite3.Connection, session_id: int, ended_at,
                     actual_duration: int, reflection: Optional[str],
                     focus_score: Optional[int]) -> None:
    if isinstance(ended_at, datetime):
        ended_at = ended_at.isoformat()
    conn.execute(
        """UPDATE sessions
           SET ended_at=?, actual_duration=?, reflection=?, focus_score=?, completed=1
           WHERE id=?""",
        (ended_at, actual_duration, reflection, focus_score, session_id),
    )
    conn.commit()


def total_hours_for_goal(conn: sqlite3.Connection, goal_id: int) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(actual_duration), 0) FROM sessions WHERE goal_id=? AND completed=1",
        (goal_id,),
    ).fetchone()
    return row[0] / 60.0


def sessions_today(conn: sqlite3.Connection, date: Optional[str] = None) -> list[sqlite3.Row]:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return conn.execute(
        "SELECT * FROM sessions WHERE DATE(started_at) = ? ORDER BY started_at",
        (date,),
    ).fetchall()


def recent_focus_scores(conn: sqlite3.Connection, limit: int = 10) -> list[float]:
    rows = conn.execute(
        """SELECT focus_score FROM sessions
           WHERE completed=1 AND focus_score IS NOT NULL AND session_type='work'
           ORDER BY started_at DESC, id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [r[0] for r in reversed(rows)]


def daily_hours(conn: sqlite3.Connection, days: int = 14) -> list[tuple[str, float]]:
    rows = conn.execute(
        """SELECT DATE(started_at) as day, SUM(actual_duration) / 60.0 as hours
           FROM sessions WHERE completed=1 AND session_type='work'
           GROUP BY day ORDER BY day DESC LIMIT ?""",
        (days,),
    ).fetchall()
    return [(r["day"], r["hours"]) for r in reversed(rows)]


def list_sessions(conn: sqlite3.Connection, goal_id: Optional[int] = None,
                  limit: int = 50) -> list[sqlite3.Row]:
    if goal_id:
        return conn.execute(
            "SELECT * FROM sessions WHERE goal_id=? ORDER BY started_at DESC LIMIT ?",
            (goal_id, limit),
        ).fetchall()
    return conn.execute(
        "SELECT s.*, g.title as goal_title FROM sessions s JOIN goals g ON s.goal_id=g.id "
        "ORDER BY s.started_at DESC LIMIT ?",
        (limit,),
    ).fetchall()


def get_setting(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def current_streak(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """SELECT DISTINCT DATE(started_at) as day FROM sessions
           WHERE completed=1 AND session_type='work'
           ORDER BY day DESC"""
    ).fetchall()
    if not rows:
        return 0
    streak = 0
    today = date.today()
    for i, row in enumerate(rows):
        expected = (today - timedelta(days=i)).isoformat()
        if row["day"] == expected:
            streak += 1
        else:
            break
    return streak
