from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from ..models import TimerStatus, SessionType


@dataclass
class PomodoroConfig:
    work_duration: int = 25 * 60
    short_break: int = 5 * 60
    long_break: int = 15 * 60
    pomodoros_per_set: int = 4


@dataclass
class TimerState:
    status: TimerStatus = TimerStatus.IDLE
    goal_id: Optional[int] = None
    task_id: Optional[int] = None
    intent: str = ""
    pomodoro_number: int = 1
    seconds_remaining: int = 0
    session_start: Optional[datetime] = None
    config: PomodoroConfig = field(default_factory=PomodoroConfig)


class PomodoroService:
    def __init__(self, config: Optional[PomodoroConfig] = None):
        self._config = config or PomodoroConfig()
        self._state = TimerState(config=self._config)
        self._subscribers: list[Callable[[TimerState], None]] = []

    @property
    def state(self) -> TimerState:
        return self._state

    def subscribe(self, callback: Callable[[TimerState], None]) -> None:
        self._subscribers.append(callback)

    def _notify(self) -> None:
        for cb in self._subscribers:
            cb(self._state)

    def begin_intent(self, goal_id: int, task_id: Optional[int] = None) -> None:
        if self._state.status != TimerStatus.IDLE:
            raise ValueError(f"Cannot begin intent from {self._state.status}")
        self._state.status = TimerStatus.INTENT
        self._state.goal_id = goal_id
        self._state.task_id = task_id
        self._notify()

    def start(self, intent: str) -> None:
        if self._state.status != TimerStatus.INTENT:
            raise ValueError(f"Cannot start from {self._state.status}")
        self._state.status = TimerStatus.RUNNING
        self._state.intent = intent
        self._state.seconds_remaining = self._config.work_duration
        self._state.session_start = datetime.now()
        self._notify()

    def pause(self) -> None:
        if self._state.status != TimerStatus.RUNNING:
            raise ValueError(f"Cannot pause from {self._state.status}")
        self._state.status = TimerStatus.PAUSED
        self._notify()

    def resume(self) -> None:
        if self._state.status != TimerStatus.PAUSED:
            raise ValueError(f"Cannot resume from {self._state.status}")
        self._state.status = TimerStatus.RUNNING
        self._notify()

    def tick(self) -> bool:
        if self._state.status not in (TimerStatus.RUNNING, TimerStatus.BREAK):
            return False
        self._state.seconds_remaining = max(0, self._state.seconds_remaining - 1)
        if self._state.seconds_remaining == 0:
            if self._state.status == TimerStatus.RUNNING:
                self._state.status = TimerStatus.REFLECTION
            else:
                self._state.pomodoro_number += 1
                self._state.status = TimerStatus.INTENT
            self._notify()
            return True
        self._notify()
        return False

    def submit_reflection(self, reflection: str, focus_score: int) -> SessionType:
        if self._state.status != TimerStatus.REFLECTION:
            raise ValueError(f"Cannot submit reflection from {self._state.status}")
        num = self._state.pomodoro_number
        if num % self._config.pomodoros_per_set == 0:
            break_type = SessionType.LONG_BREAK
            duration = self._config.long_break
        else:
            break_type = SessionType.SHORT_BREAK
            duration = self._config.short_break
        self._state.status = TimerStatus.BREAK
        self._state.seconds_remaining = duration
        self._notify()
        return break_type

    def skip_break(self) -> None:
        if self._state.status != TimerStatus.BREAK:
            raise ValueError(f"Cannot skip break from {self._state.status}")
        self._state.status = TimerStatus.RUNNING
        self._state.seconds_remaining = self._config.work_duration
        self._notify()

    def abandon(self) -> None:
        self._state = TimerState(config=self._config)
        self._notify()

    def finish(self) -> None:
        self._state = TimerState(config=self._config)
        self._notify()
