from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class TimerStatus(Enum):
    IDLE = auto()
    INTENT = auto()
    RUNNING = auto()
    PAUSED = auto()
    BREAK = auto()
    REFLECTION = auto()


class SessionType(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass
class Goal:
    id: int
    title: str
    description: str
    target_hours: float
    color: str
    created_at: datetime
    archived: bool = False


@dataclass
class Task:
    id: int
    goal_id: int
    title: str
    completed: bool
    created_at: datetime


@dataclass
class Session:
    id: int
    goal_id: int
    started_at: datetime
    planned_duration: int
    session_type: SessionType
    pomodoro_number: int
    intent: Optional[str] = None
    reflection: Optional[str] = None
    focus_score: Optional[int] = None
    actual_duration: Optional[int] = None
    ended_at: Optional[datetime] = None
    completed: bool = False
    task_id: Optional[int] = None
