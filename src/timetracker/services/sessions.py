import sqlite3
from datetime import datetime
from typing import Optional
from ..db import queries


class SessionService:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def start(self, goal_id: int, intent: str, pomodoro_number: int,
              planned_duration: int, started_at: Optional[datetime] = None,
              task_id: Optional[int] = None) -> int:
        return queries.create_session(
            self._conn, goal_id=goal_id,
            started_at=started_at or datetime.now(),
            planned_duration=planned_duration, session_type="work",
            pomodoro_number=pomodoro_number, intent=intent, task_id=task_id,
        )

    def complete(self, session_id: int, ended_at: datetime, actual_duration: int,
                 reflection: Optional[str], focus_score: Optional[int]) -> None:
        queries.complete_session(
            self._conn, session_id=session_id, ended_at=ended_at,
            actual_duration=actual_duration, reflection=reflection,
            focus_score=focus_score,
        )

    def today_summary(self) -> dict:
        sessions = queries.sessions_today(self._conn)
        completed = [s for s in sessions if s["completed"] == 1 and s["session_type"] == "work"]
        return {
            "completed_pomodoros": len(completed),
            "total_minutes": sum(s["actual_duration"] or 0 for s in completed),
            "sessions": sessions,
        }

    def recent_focus_scores(self, limit: int = 10) -> list[float]:
        return queries.recent_focus_scores(self._conn, limit)

    def daily_hours(self, days: int = 14) -> list[tuple[str, float]]:
        return queries.daily_hours(self._conn, days)

    def streak(self) -> int:
        return queries.current_streak(self._conn)
