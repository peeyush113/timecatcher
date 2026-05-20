import sqlite3
from datetime import datetime
from typing import Optional
from ..models import Goal
from ..db import queries


class GoalService:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, title: str, description: str = "", target_hours: float = 0,
               color: str = "#4CAF50") -> Goal:
        gid = queries.create_goal(self._conn, title, description, target_hours, color)
        row = queries.get_goal(self._conn, gid)
        return Goal(
            id=row["id"], title=row["title"], description=row["description"],
            target_hours=row["target_hours"], color=row["color"],
            created_at=datetime.fromisoformat(row["created_at"]),
            archived=bool(row["archived"]),
        )

    def list_active(self) -> list[Goal]:
        rows = queries.list_goals(self._conn)
        return [
            Goal(id=r["id"], title=r["title"], description=r["description"],
                 target_hours=r["target_hours"], color=r["color"],
                 created_at=datetime.fromisoformat(r["created_at"]),
                 archived=bool(r["archived"]))
            for r in rows
        ]

    def progress_pct(self, goal_id: int) -> float:
        row = queries.get_goal(self._conn, goal_id)
        if not row or row["target_hours"] == 0:
            return 0.0
        logged = queries.total_hours_for_goal(self._conn, goal_id)
        return min(100.0, (logged / row["target_hours"]) * 100)

    def archive(self, goal_id: int) -> None:
        queries.archive_goal(self._conn, goal_id)
