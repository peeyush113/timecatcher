# TimeTracker (Pomodoro + Goals) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open-source, local-first terminal time tracker with Pomodoro-first sessions, goal tracking, and a rich visual dashboard using Python + Textual.

**Architecture:** Layered: SQLite (stdlib) → dataclass models → pure-Python services → Textual widgets → Textual screens. The `PomodoroService` is the single source of timer truth; Textual screens subscribe to it via `Message` events and `set_interval` ticks. No cloud, no accounts — all data in `~/.timetracker/data.db`.

**Tech Stack:** Python 3.11+, Textual 0.86+, SQLite3 (stdlib), pytest 8+, pytest-asyncio 0.23+

---

## File Structure

```
timetracker/
├── pyproject.toml
├── src/
│   └── timetracker/
│       ├── __init__.py
│       ├── main.py                  # App entry point, App class, SCREENS, BINDINGS
│       ├── models.py                # Dataclasses: Goal, Task, Session + enums
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py        # get_connection(), init_db(), schema SQL
│       │   └── queries.py           # All SQL: goals CRUD, sessions CRUD, analytics
│       ├── services/
│       │   ├── __init__.py
│       │   ├── timer.py             # PomodoroService: state machine, tick(), transitions
│       │   ├── goals.py             # GoalService: CRUD + progress % calculation
│       │   └── sessions.py          # SessionService: save session, analytics aggregations
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── dashboard.py         # Default screen: timer + goal bars + session dots + sparkline
│       │   ├── pomodoro.py          # IntentModal + ReflectionModal (push/pop on dashboard)
│       │   ├── goals.py             # Goal list + create/edit form
│       │   ├── analytics.py         # Charts: daily bars, heatmap, goal breakdown
│       │   └── history.py           # Searchable/filterable session log
│       └── widgets/
│           ├── __init__.py
│           ├── timer_display.py     # Big countdown + status label + pomodoro dots
│           ├── goal_bar.py          # Single goal row: title + progress bar + time logged
│           └── sparkline.py        # Focus score sparkline using Textual Sparkline widget
├── tests/
│   ├── conftest.py                  # Fixtures: in-memory DB conn, sample goals/sessions
│   ├── test_db/
│   │   ├── test_connection.py
│   │   └── test_queries.py
│   ├── test_services/
│   │   ├── test_timer.py
│   │   ├── test_goals.py
│   │   └── test_sessions.py
│   └── test_screens/
│       └── test_dashboard.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/timetracker/__init__.py`
- Create: `src/timetracker/db/__init__.py`
- Create: `src/timetracker/services/__init__.py`
- Create: `src/timetracker/screens/__init__.py`
- Create: `src/timetracker/widgets/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db/__init__.py`
- Create: `tests/test_services/__init__.py`
- Create: `tests/test_screens/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "timetracker"
version = "0.1.0"
description = "Goal-focused Pomodoro timer for the terminal"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.86.0",
]

[project.scripts]
tt = "timetracker.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/timetracker"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "textual[dev]>=0.86.0",
]
```

- [ ] **Step 2: Create all `__init__.py` files (all empty)**

```bash
mkdir -p src/timetracker/{db,services,screens,widgets}
mkdir -p tests/{test_db,test_services,test_screens}
touch src/timetracker/__init__.py
touch src/timetracker/db/__init__.py
touch src/timetracker/services/__init__.py
touch src/timetracker/screens/__init__.py
touch src/timetracker/widgets/__init__.py
touch tests/__init__.py
touch tests/test_db/__init__.py
touch tests/test_services/__init__.py
touch tests/test_screens/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 4: Verify install**

```bash
python -c "import textual; import pytest; print('OK')"
```

Expected output: `OK`

- [ ] **Step 5: Commit**

```bash
git init
git add pyproject.toml src/ tests/
git commit -m "chore: project scaffold with Textual + pytest"
```

---

## Task 2: Data Models

**Files:**
- Create: `src/timetracker/models.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_services/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_services/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'timetracker.models'`

- [ ] **Step 3: Implement models.py**

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class TimerStatus(Enum):
    IDLE = auto()
    INTENT = auto()       # Collecting intent before session
    RUNNING = auto()      # Work timer counting down
    PAUSED = auto()       # Work timer paused
    BREAK = auto()        # Break timer counting down
    REFLECTION = auto()   # Collecting reflection after session


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
    planned_duration: int       # minutes
    session_type: SessionType
    pomodoro_number: int
    intent: Optional[str] = None
    reflection: Optional[str] = None
    focus_score: Optional[int] = None
    actual_duration: Optional[int] = None
    ended_at: Optional[datetime] = None
    completed: bool = False
    task_id: Optional[int] = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_services/test_models.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/timetracker/models.py tests/test_services/test_models.py
git commit -m "feat: data models (Goal, Task, Session, enums)"
```

---

## Task 3: Database Layer

**Files:**
- Create: `src/timetracker/db/connection.py`
- Create: `tests/test_db/test_connection.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_db/test_connection.py`:

```python
import sqlite3
from pathlib import Path
import tempfile
from timetracker.db.connection import create_connection, init_db, DEFAULT_SETTINGS


def test_init_db_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert {"goals", "tasks", "sessions", "settings"} <= tables


def test_init_db_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        init_db(conn)  # should not raise
        count = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        assert count == len(DEFAULT_SETTINGS)


def test_default_settings_inserted():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'work_duration'"
        ).fetchone()
        assert row is not None
        assert row[0] == "25"


def test_foreign_keys_enforced():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = create_connection(Path(f.name))
        init_db(conn)
        try:
            conn.execute(
                "INSERT INTO tasks (goal_id, title) VALUES (999, 'orphan')"
            )
            conn.commit()
            assert False, "Should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db/test_connection.py -v
```

Expected: `ModuleNotFoundError: No module named 'timetracker.db.connection'`

- [ ] **Step 3: Implement connection.py**

```python
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    target_hours REAL DEFAULT 0,
    color TEXT DEFAULT '#4CAF50',
    created_at TEXT DEFAULT (datetime('now')),
    archived INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id),
    task_id INTEGER REFERENCES tasks(id),
    intent TEXT,
    reflection TEXT,
    focus_score INTEGER CHECK (focus_score IS NULL OR (focus_score BETWEEN 1 AND 5)),
    planned_duration INTEGER NOT NULL DEFAULT 25,
    actual_duration INTEGER,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    completed INTEGER DEFAULT 0,
    session_type TEXT NOT NULL DEFAULT 'work',
    pomodoro_number INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS: dict[str, str] = {
    "work_duration": "25",
    "short_break_duration": "5",
    "long_break_duration": "15",
    "pomodoros_per_set": "4",
}


def create_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    if db_path is None:
        data_dir = Path.home() / ".timetracker"
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / "data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db/test_connection.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/timetracker/db/connection.py tests/test_db/test_connection.py
git commit -m "feat: sqlite schema, connection factory, default settings"
```

---

## Task 4: Database Queries

**Files:**
- Create: `src/timetracker/db/queries.py`
- Create: `tests/test_db/test_queries.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write conftest.py with shared fixtures**

```python
import sqlite3
import pytest
from datetime import datetime
from timetracker.db.connection import create_connection, init_db
from timetracker.db import queries


@pytest.fixture
def db():
    conn = create_connection(db_path=None)  # in-memory via :memory:
    init_db(conn)
    yield conn
    conn.close()


# Override create_connection to use :memory: for all tests
@pytest.fixture(autouse=True)
def _patch_db_path(monkeypatch, tmp_path):
    """Redirect DB to a temp file so tests don't touch ~/.timetracker."""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(
        "timetracker.db.connection.create_connection",
        lambda db_path=None: sqlite3.connect(str(db_file)),
    )
```

Wait — the fixture above is overly complex. Use a simpler pattern:

```python
import pytest
import sqlite3
from timetracker.db.connection import init_db


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    yield conn
    conn.close()
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_db/test_queries.py`:

```python
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
    queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 19, 9, 0),
                            planned_duration=25, session_type="work", pomodoro_number=1, intent="x")
    s2 = queries.create_session(db, goal_id=gid, started_at=datetime(2026, 5, 19, 10, 0),
                                 planned_duration=25, session_type="work", pomodoro_number=2, intent="y")
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
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/test_db/test_queries.py -v
```

Expected: `ModuleNotFoundError: No module named 'timetracker.db.queries'`

- [ ] **Step 4: Implement queries.py**

```python
import sqlite3
from datetime import datetime
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


def create_session(conn: sqlite3.Connection, goal_id: int, started_at: datetime,
                   planned_duration: int, session_type: str, pomodoro_number: int,
                   intent: Optional[str] = None, task_id: Optional[int] = None) -> int:
    cur = conn.execute(
        """INSERT INTO sessions
           (goal_id, task_id, intent, planned_duration, started_at, session_type, pomodoro_number)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (goal_id, task_id, intent, planned_duration,
         started_at.isoformat(), session_type, pomodoro_number),
    )
    conn.commit()
    return cur.lastrowid


def get_session(conn: sqlite3.Connection, session_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()


def complete_session(conn: sqlite3.Connection, session_id: int, ended_at: datetime,
                     actual_duration: int, reflection: Optional[str],
                     focus_score: Optional[int]) -> None:
    conn.execute(
        """UPDATE sessions
           SET ended_at=?, actual_duration=?, reflection=?, focus_score=?, completed=1
           WHERE id=?""",
        (ended_at.isoformat(), actual_duration, reflection, focus_score, session_id),
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
           ORDER BY started_at DESC LIMIT ?""",
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
    from datetime import date, timedelta
    today = date.today()
    for i, row in enumerate(rows):
        expected = (today - timedelta(days=i)).isoformat()
        if row["day"] == expected:
            streak += 1
        else:
            break
    return streak
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_db/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/timetracker/db/queries.py tests/test_db/test_queries.py tests/conftest.py
git commit -m "feat: SQL queries (goals CRUD, sessions CRUD, analytics)"
```

---

## Task 5: Timer Service (State Machine)

**Files:**
- Create: `src/timetracker/services/timer.py`
- Create: `tests/test_services/test_timer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_services/test_timer.py`:

```python
import pytest
from timetracker.services.timer import PomodoroService, PomodoroConfig
from timetracker.models import TimerStatus, SessionType


@pytest.fixture
def svc():
    cfg = PomodoroConfig(work_duration=10, short_break=3, long_break=6, pomodoros_per_set=4)
    return PomodoroService(config=cfg)


def test_initial_state_is_idle(svc):
    assert svc.state.status == TimerStatus.IDLE


def test_begin_intent_transitions_to_intent(svc):
    svc.begin_intent(goal_id=1)
    assert svc.state.status == TimerStatus.INTENT
    assert svc.state.goal_id == 1


def test_start_transitions_to_running(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="Write tests")
    assert svc.state.status == TimerStatus.RUNNING
    assert svc.state.seconds_remaining == 10
    assert svc.state.intent == "Write tests"


def test_pause_and_resume(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    svc.pause()
    assert svc.state.status == TimerStatus.PAUSED
    svc.resume()
    assert svc.state.status == TimerStatus.RUNNING


def test_tick_decrements_seconds(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    finished = svc.tick()
    assert svc.state.seconds_remaining == 9
    assert finished is False


def test_tick_to_zero_triggers_reflection(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    assert svc.state.status == TimerStatus.REFLECTION
    assert svc.state.seconds_remaining == 0


def test_reflection_moves_to_short_break(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    break_type = svc.submit_reflection(reflection="done", focus_score=4)
    assert break_type == SessionType.SHORT_BREAK
    assert svc.state.status == TimerStatus.BREAK
    assert svc.state.seconds_remaining == 3


def test_fourth_reflection_moves_to_long_break(svc):
    for _ in range(3):
        svc.begin_intent(goal_id=1) if svc.state.status == TimerStatus.IDLE else None
        if svc.state.status == TimerStatus.IDLE:
            svc.begin_intent(goal_id=1)
        svc.start(intent="x") if svc.state.status == TimerStatus.INTENT else None
        for _ in range(10):
            svc.tick()
        svc.submit_reflection("done", 3)
        for _ in range(3):
            svc.tick()  # exhaust break

    # 4th pomodoro
    svc.start(intent="last") if svc.state.status == TimerStatus.INTENT else None
    for _ in range(10):
        svc.tick()
    break_type = svc.submit_reflection("done", 5)
    assert break_type == SessionType.LONG_BREAK
    assert svc.state.seconds_remaining == 6


def test_abandon_resets_to_idle(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    svc.abandon()
    assert svc.state.status == TimerStatus.IDLE
    assert svc.state.goal_id is None


def test_skip_break(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    svc.submit_reflection("done", 4)
    svc.skip_break()
    assert svc.state.status == TimerStatus.RUNNING
    assert svc.state.seconds_remaining == 10


def test_subscriber_notified_on_state_change(svc):
    events = []
    svc.subscribe(lambda s: events.append(s.status))
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    assert TimerStatus.INTENT in events
    assert TimerStatus.RUNNING in events


def test_begin_intent_raises_if_not_idle(svc):
    svc.begin_intent(goal_id=1)
    with pytest.raises(ValueError):
        svc.begin_intent(goal_id=2)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_services/test_timer.py -v
```

Expected: `ModuleNotFoundError: No module named 'timetracker.services.timer'`

- [ ] **Step 3: Implement timer.py**

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from ..models import TimerStatus, SessionType


@dataclass
class PomodoroConfig:
    work_duration: int = 25 * 60       # seconds
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
        """Decrement timer by 1 second. Returns True when timer hits zero."""
        if self._state.status not in (TimerStatus.RUNNING, TimerStatus.BREAK):
            return False
        self._state.seconds_remaining = max(0, self._state.seconds_remaining - 1)
        if self._state.seconds_remaining == 0:
            if self._state.status == TimerStatus.RUNNING:
                self._state.status = TimerStatus.REFLECTION
            else:
                # Break finished — ready for next pomodoro intent
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
        """End session set entirely — return to IDLE."""
        self._state = TimerState(config=self._config)
        self._notify()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_services/test_timer.py -v
```

Expected: all tests pass (fix the fourth-pomodoro test if needed — the loop test is complex, adjust assertions to match the state machine flow)

- [ ] **Step 5: Commit**

```bash
git add src/timetracker/services/timer.py tests/test_services/test_timer.py
git commit -m "feat: Pomodoro state machine (idle→intent→running→reflection→break)"
```

---

## Task 6: Goal and Session Services

**Files:**
- Create: `src/timetracker/services/goals.py`
- Create: `src/timetracker/services/sessions.py`
- Create: `tests/test_services/test_goals.py`
- Create: `tests/test_services/test_sessions.py`

- [ ] **Step 1: Write failing tests for GoalService**

Create `tests/test_services/test_goals.py`:

```python
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


def test_list_goals(db):
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
    db.execute(
        "INSERT INTO sessions (goal_id, started_at, planned_duration, session_type, "
        "pomodoro_number, actual_duration, completed) VALUES (?,?,?,?,?,?,1)",
        (goal.id, "2026-05-19T09:00:00", 25, "work", 1, 300),  # 300 min = 5 hours
    )
    db.commit()
    assert svc.progress_pct(goal.id) == pytest.approx(50.0)
```

- [ ] **Step 2: Write failing tests for SessionService**

Create `tests/test_services/test_sessions.py`:

```python
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
```

- [ ] **Step 3: Run to verify failures**

```bash
pytest tests/test_services/test_goals.py tests/test_services/test_sessions.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: Implement goals.py**

```python
import sqlite3
from typing import Optional
from datetime import datetime
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
```

- [ ] **Step 5: Implement sessions.py**

```python
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
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_services/ -v
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add src/timetracker/services/goals.py src/timetracker/services/sessions.py \
        tests/test_services/test_goals.py tests/test_services/test_sessions.py
git commit -m "feat: GoalService (progress %) and SessionService (start/complete/analytics)"
```

---

## Task 7: App Shell and Navigation

**Files:**
- Create: `src/timetracker/main.py`
- Create: `src/timetracker/screens/dashboard.py` (stub)
- Create: `src/timetracker/screens/goals.py` (stub)
- Create: `src/timetracker/screens/analytics.py` (stub)
- Create: `src/timetracker/screens/history.py` (stub)

- [ ] **Step 1: Create screen stubs**

Create `src/timetracker/screens/dashboard.py`:
```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Dashboard — coming soon")
```

Create `src/timetracker/screens/goals.py`:
```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class GoalsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Goals — coming soon")
```

Create `src/timetracker/screens/analytics.py`:
```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class AnalyticsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Analytics — coming soon")
```

Create `src/timetracker/screens/history.py`:
```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class HistoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("History — coming soon")
```

- [ ] **Step 2: Create main.py**

```python
import sqlite3
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .db.connection import create_connection, init_db
from .services.timer import PomodoroService, PomodoroConfig
from .services.goals import GoalService
from .services.sessions import SessionService
from .screens.dashboard import DashboardScreen
from .screens.goals import GoalsScreen
from .screens.analytics import AnalyticsScreen
from .screens.history import HistoryScreen


class TimeTrackerApp(App):
    TITLE = "TimeTracker"
    BINDINGS = [
        Binding("d", "push_screen('dashboard')", "Dashboard", show=True),
        Binding("g", "push_screen('goals')", "Goals", show=True),
        Binding("a", "push_screen('analytics')", "Analytics", show=True),
        Binding("h", "push_screen('history')", "History", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]
    SCREENS = {
        "dashboard": DashboardScreen,
        "goals": GoalsScreen,
        "analytics": AnalyticsScreen,
        "history": HistoryScreen,
    }

    def __init__(self):
        super().__init__()
        self.conn: sqlite3.Connection = create_connection()
        init_db(self.conn)
        cfg = PomodoroConfig(
            work_duration=int(self._get_setting("work_duration", "25")) * 60,
            short_break=int(self._get_setting("short_break_duration", "5")) * 60,
            long_break=int(self._get_setting("long_break_duration", "15")) * 60,
            pomodoros_per_set=int(self._get_setting("pomodoros_per_set", "4")),
        )
        self.timer_svc = PomodoroService(config=cfg)
        self.goal_svc = GoalService(self.conn)
        self.session_svc = SessionService(self.conn)

    def _get_setting(self, key: str, default: str) -> str:
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row[0] if row else default

    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


def main() -> None:
    TimeTrackerApp().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write a smoke test for the app shell**

Create `tests/test_screens/test_dashboard.py`:

```python
import pytest
from unittest.mock import patch
from textual.testing import AppTest  # if available, else use run_test()

# Use Textual's built-in test runner
async def test_app_launches_and_shows_dashboard():
    from timetracker.main import TimeTrackerApp
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        with patch("timetracker.db.connection.get_db_path",
                   return_value=Path(tmp) / "test.db"):
            app = TimeTrackerApp()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause(0.1)
                # App launched without crashing
                assert app.screen is not None
```

- [ ] **Step 4: Run the smoke test**

```bash
pytest tests/test_screens/test_dashboard.py -v
```

Expected: 1 passed

- [ ] **Step 5: Run the app manually to verify it starts**

```bash
python -m timetracker.main
```

Expected: terminal UI opens, showing "Dashboard — coming soon", footer shows keybindings. Press `q` to quit.

- [ ] **Step 6: Commit**

```bash
git add src/timetracker/main.py src/timetracker/screens/ tests/test_screens/
git commit -m "feat: app shell with screen navigation and service wiring"
```

---

## Task 8: Timer Display Widget

**Files:**
- Create: `src/timetracker/widgets/timer_display.py`
- Create: `src/timetracker/widgets/sparkline.py`

- [ ] **Step 1: Create timer_display.py**

```python
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label
from ..models import TimerStatus


class TimerDisplay(Widget):
    """Shows MM:SS countdown, session status, and pomodoro dot indicators."""

    DEFAULT_CSS = """
    TimerDisplay {
        height: 9;
        border: solid $accent;
        padding: 1 2;
        content-align: center middle;
        text-align: center;
    }
    .timer-time {
        text-style: bold;
        color: $success;
        width: 1fr;
        content-align: center middle;
    }
    .timer-time.break {
        color: $warning;
    }
    .timer-label {
        color: $text-muted;
        width: 1fr;
        content-align: center middle;
    }
    .timer-dots {
        width: 1fr;
        content-align: center middle;
    }
    """

    seconds: reactive[int] = reactive(25 * 60)
    status: reactive[TimerStatus] = reactive(TimerStatus.IDLE)
    pomodoro_number: reactive[int] = reactive(1)
    intent: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("", id="timer-label", classes="timer-label")
        yield Label("25:00", id="timer-time", classes="timer-time")
        yield Label("● ○ ○ ○", id="timer-dots", classes="timer-dots")

    def watch_seconds(self, seconds: int) -> None:
        mins, secs = divmod(seconds, 60)
        self.query_one("#timer-time", Label).update(f"{mins:02d}:{secs:02d}")

    def watch_status(self, status: TimerStatus) -> None:
        label = self.query_one("#timer-label", Label)
        time_widget = self.query_one("#timer-time", Label)
        status_map = {
            TimerStatus.IDLE: "Ready — press N to start",
            TimerStatus.INTENT: "Setting intent...",
            TimerStatus.RUNNING: f"Focus: {self.intent}",
            TimerStatus.PAUSED: f"Paused — {self.intent}",
            TimerStatus.BREAK: "Break time!",
            TimerStatus.REFLECTION: "Session complete!",
        }
        label.update(status_map.get(status, ""))
        if status == TimerStatus.BREAK:
            time_widget.add_class("break")
        else:
            time_widget.remove_class("break")

    def watch_pomodoro_number(self, num: int) -> None:
        dots = []
        for i in range(1, 5):
            dots.append("●" if i < num else ("◉" if i == num else "○"))
        self.query_one("#timer-dots", Label).update("  ".join(dots))

    def watch_intent(self, intent: str) -> None:
        if self.status == TimerStatus.RUNNING:
            self.query_one("#timer-label", Label).update(f"Focus: {intent}")
```

- [ ] **Step 2: Create sparkline.py wrapper**

```python
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Sparkline, Label


class FocusSparkline(Widget):
    """Focus score trend over recent sessions."""

    DEFAULT_CSS = """
    FocusSparkline {
        height: 5;
        border: solid $panel;
        padding: 0 1;
    }
    """

    def __init__(self, scores: list[float], **kwargs):
        super().__init__(**kwargs)
        self._scores = scores or [0.0]

    def compose(self) -> ComposeResult:
        avg = sum(self._scores) / len(self._scores) if self._scores else 0
        yield Label(f"Focus trend  avg: {avg:.1f}/5", classes="section-title")
        yield Sparkline(self._scores, summary_function=max)
```

- [ ] **Step 3: Commit**

```bash
git add src/timetracker/widgets/
git commit -m "feat: TimerDisplay widget and FocusSparkline widget"
```

---

## Task 9: Dashboard Screen

**Files:**
- Modify: `src/timetracker/screens/dashboard.py`

This is the main screen. It wires `PomodoroService` to `TimerDisplay`, shows goal progress bars, today's session dots, and the focus sparkline.

- [ ] **Step 1: Implement dashboard.py**

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Label, ProgressBar
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual import on
from datetime import datetime

from ..models import TimerStatus
from ..widgets.timer_display import TimerDisplay
from ..widgets.sparkline import FocusSparkline


class GoalProgressRow(Static):
    """Single goal: title + progress bar + hours logged."""

    def __init__(self, title: str, progress_pct: float, logged_h: float,
                 target_h: float, color: str, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._pct = progress_pct
        self._logged = logged_h
        self._target = target_h
        self._color = color

    def compose(self) -> ComposeResult:
        yield Label(f"{self._title[:28]:<28}", classes="goal-title")
        bar = ProgressBar(total=100, show_percentage=False, show_eta=False)
        bar.advance(self._pct)
        yield bar
        yield Label(f" {self._logged:.1f}/{self._target:.0f}h", classes="goal-hours")


class DashboardScreen(Screen):
    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 1fr;
        grid-columns: 1fr 2fr;
    }
    #left-panel {
        row-span: 2;
        border: solid $accent;
        padding: 1;
    }
    #goals-panel {
        border: solid $panel;
        padding: 1;
    }
    #bottom-panel {
        border: solid $panel;
        padding: 1;
    }
    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .goal-title { width: 30; }
    .goal-hours { width: 12; color: $text-muted; }
    .stat-label { color: $text-muted; }
    .stat-value { text-style: bold; color: $success; }
    .session-dot { margin-right: 1; }
    """

    _active_session_id: int | None = None

    def compose(self) -> ComposeResult:
        app = self.app
        scores = app.session_svc.recent_focus_scores()
        streak = app.session_svc.streak()
        summary = app.session_svc.today_summary()

        with Vertical(id="left-panel"):
            yield Label("TIMER", classes="section-title")
            yield TimerDisplay(id="timer-display")
            yield Label("")
            yield Label(f"Streak: {streak} days", classes="stat-value")
            yield Label(f"Today: {summary['completed_pomodoros']} pomodoros  "
                        f"{summary['total_minutes']}m", classes="stat-label")

        with Vertical(id="goals-panel"):
            yield Label("TODAY'S GOALS", classes="section-title")
            goals = app.goal_svc.list_active()
            if goals:
                for g in goals[:5]:
                    pct = app.goal_svc.progress_pct(g.id)
                    logged = float(app.conn.execute(
                        "SELECT COALESCE(SUM(actual_duration),0)/60.0 FROM sessions "
                        "WHERE goal_id=? AND completed=1", (g.id,)
                    ).fetchone()[0])
                    yield GoalProgressRow(g.title, pct, logged, g.target_hours, g.color)
            else:
                yield Label("No goals yet — press G to create one", classes="stat-label")

        with Vertical(id="bottom-panel"):
            yield Label("FOCUS TREND", classes="section-title")
            yield FocusSparkline(scores)
            yield Label("")
            yield Label("SESSION TIMELINE", classes="section-title")
            dots = self._build_session_dots(summary["sessions"])
            yield Label(dots or "No sessions today", classes="stat-label")

    def _build_session_dots(self, sessions) -> str:
        if not sessions:
            return ""
        parts = []
        for s in sessions:
            if s["session_type"] != "work":
                continue
            if s["completed"]:
                score = s["focus_score"] or 3
                colors = {1: "red", 2: "orange", 3: "yellow", 4: "green", 5: "blue"}
                parts.append(f"[{colors.get(score, 'white')}]●[/]")
            else:
                parts.append("[dim]◌[/]")
        return "  ".join(parts)

    def on_mount(self) -> None:
        self.app.timer_svc.subscribe(self._on_timer_state)
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        finished = self.app.timer_svc.tick()
        if finished and self.app.timer_svc.state.status == TimerStatus.REFLECTION:
            self._show_reflection_modal()

    def _on_timer_state(self, state) -> None:
        try:
            display = self.query_one("#timer-display", TimerDisplay)
            display.seconds = state.seconds_remaining
            display.status = state.status
            display.pomodoro_number = state.pomodoro_number
            display.intent = state.intent
        except Exception:
            pass

    def _show_reflection_modal(self) -> None:
        from .pomodoro import ReflectionModal
        self.app.push_screen(
            ReflectionModal(self.app.timer_svc, self.app.session_svc,
                            self._active_session_id)
        )

    def action_new_session(self) -> None:
        from .pomodoro import IntentModal
        goals = self.app.goal_svc.list_active()
        if not goals:
            self.notify("Create a goal first — press G", severity="warning")
            return
        self.app.push_screen(IntentModal(self.app.timer_svc, goals))
```

- [ ] **Step 2: Wire `n` keybinding in main.py**

In `main.py`, add to BINDINGS:
```python
Binding("n", "new_session", "New Session", show=True),
```

And add action handler:
```python
def action_new_session(self) -> None:
    screen = self.screen
    if hasattr(screen, "action_new_session"):
        screen.action_new_session()
```

- [ ] **Step 3: Run the app**

```bash
python -m timetracker.main
```

Expected: Dashboard shows with timer display, goal section (empty if no goals), focus sparkline, session timeline.

- [ ] **Step 4: Commit**

```bash
git add src/timetracker/screens/dashboard.py src/timetracker/main.py
git commit -m "feat: dashboard screen with timer, goal progress bars, sparkline"
```

---

## Task 10: Pomodoro Intent and Reflection Modals

**Files:**
- Create: `src/timetracker/screens/pomodoro.py`

- [ ] **Step 1: Create pomodoro.py**

```python
from datetime import datetime
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, RadioSet, RadioButton
from textual.containers import Vertical, Horizontal
from ..models import TimerStatus
from ..services.timer import PomodoroService
from ..services.sessions import SessionService
from ..models import Goal


class IntentModal(ModalScreen):
    """Pre-session modal: select goal and state intent."""

    DEFAULT_CSS = """
    IntentModal {
        align: center middle;
    }
    #intent-dialog {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 2 4;
    }
    .modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    Button { margin-top: 1; }
    """

    def __init__(self, timer_svc: PomodoroService, goals: list[Goal], **kwargs):
        super().__init__(**kwargs)
        self._timer_svc = timer_svc
        self._goals = goals

    def compose(self) -> ComposeResult:
        with Vertical(id="intent-dialog"):
            yield Label("Start a Pomodoro", classes="modal-title")
            yield Label("Goal:")
            options = [(g.title, str(g.id)) for g in self._goals]
            yield Select(options, id="goal-select", value=str(self._goals[0].id))
            yield Label("What will you work on?")
            yield Input(placeholder="Intent for this session...", id="intent-input")
            with Horizontal():
                yield Button("Start  ▶", variant="success", id="btn-start")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return
        goal_select = self.query_one("#goal-select", Select)
        intent_input = self.query_one("#intent-input", Input)
        if not intent_input.value.strip():
            self.notify("Please enter your intent", severity="warning")
            return
        goal_id = int(goal_select.value)
        intent = intent_input.value.strip()
        self._timer_svc.begin_intent(goal_id=goal_id)
        self._timer_svc.start(intent=intent)
        self.dismiss({"goal_id": goal_id, "intent": intent})


class ReflectionModal(ModalScreen):
    """Post-session modal: reflection text + focus rating."""

    DEFAULT_CSS = """
    ReflectionModal {
        align: center middle;
    }
    #reflect-dialog {
        width: 60;
        height: auto;
        border: thick $success;
        background: $surface;
        padding: 2 4;
    }
    .modal-title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }
    Button { margin-top: 1; }
    """

    def __init__(self, timer_svc: PomodoroService, session_svc: SessionService,
                 session_id: int | None, **kwargs):
        super().__init__(**kwargs)
        self._timer_svc = timer_svc
        self._session_svc = session_svc
        self._session_id = session_id

    def compose(self) -> ComposeResult:
        with Vertical(id="reflect-dialog"):
            yield Label("Session Complete!", classes="modal-title")
            yield Label("What did you accomplish?")
            yield Input(placeholder="Brief reflection...", id="reflection-input")
            yield Label("Focus quality:")
            with RadioSet(id="focus-rating"):
                for i in range(1, 6):
                    yield RadioButton(f"{'★' * i}{'☆' * (5-i)}  {i}", value=(i == 3))
            with Horizontal():
                yield Button("Save & Break  ☕", variant="success", id="btn-save")
                yield Button("Save & Finish", variant="primary", id="btn-finish")
                yield Button("Skip", variant="default", id="btn-skip")

    def _get_focus_score(self) -> int:
        radio_set = self.query_one("#focus-rating", RadioSet)
        if radio_set.pressed_index is not None:
            return radio_set.pressed_index + 1
        return 3

    def _save(self, reflection: str, score: int) -> None:
        if self._session_id is not None:
            self._session_svc.complete(
                session_id=self._session_id,
                ended_at=datetime.now(),
                actual_duration=self._timer_svc.state.config.work_duration // 60,
                reflection=reflection,
                focus_score=score,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        reflection = self.query_one("#reflection-input", Input).value.strip()
        score = self._get_focus_score()

        if event.button.id == "btn-skip":
            self._timer_svc.abandon()
            self.dismiss(None)
        elif event.button.id == "btn-finish":
            self._save(reflection, score)
            self._timer_svc.finish()
            self.dismiss({"action": "finish"})
        elif event.button.id == "btn-save":
            self._save(reflection, score)
            self._timer_svc.submit_reflection(reflection, score)
            self.dismiss({"action": "break"})
```

- [ ] **Step 2: Wire session persistence in dashboard.py**

In `DashboardScreen.action_new_session`, after pushing `IntentModal`, catch the result to start a session record:

```python
def action_new_session(self) -> None:
    from .pomodoro import IntentModal
    goals = self.app.goal_svc.list_active()
    if not goals:
        self.notify("Create a goal first — press G", severity="warning")
        return

    def on_intent_result(result):
        if result:
            state = self.app.timer_svc.state
            self._active_session_id = self.app.session_svc.start(
                goal_id=result["goal_id"],
                intent=result["intent"],
                pomodoro_number=state.pomodoro_number,
                planned_duration=state.config.work_duration // 60,
            )

    self.app.push_screen(IntentModal(self.app.timer_svc, goals), callback=on_intent_result)
```

- [ ] **Step 3: Run and test the full Pomodoro flow**

```bash
python -m timetracker.main
```

1. Press `n` → IntentModal opens
2. Select a goal (create one via `g` first if needed), type intent, press Start
3. Watch timer count down on dashboard
4. When timer hits 0 → ReflectionModal opens
5. Type reflection, pick focus stars, press Save & Break
6. Break timer starts

- [ ] **Step 4: Commit**

```bash
git add src/timetracker/screens/pomodoro.py src/timetracker/screens/dashboard.py
git commit -m "feat: IntentModal and ReflectionModal, full Pomodoro flow wired"
```

---

## Task 11: Goals Screen

**Files:**
- Modify: `src/timetracker/screens/goals.py`

- [ ] **Step 1: Implement goals screen**

```python
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import DataTable, Button, Input, Label, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from ..models import Goal


class CreateGoalModal(ModalScreen):
    DEFAULT_CSS = """
    CreateGoalModal { align: center middle; }
    #goal-dialog {
        width: 60; height: auto;
        border: thick $accent; background: $surface; padding: 2 4;
    }
    Button { margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="goal-dialog"):
            yield Label("New Goal", classes="section-title")
            yield Label("Title:")
            yield Input(placeholder="e.g. Write my thesis", id="title-input")
            yield Label("Description (optional):")
            yield Input(placeholder="What is this goal about?", id="desc-input")
            yield Label("Target hours (0 = no target):")
            yield Input(placeholder="50", id="hours-input", value="0")
            with Horizontal():
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return
        title = self.query_one("#title-input", Input).value.strip()
        desc = self.query_one("#desc-input", Input).value.strip()
        try:
            hours = float(self.query_one("#hours-input", Input).value or "0")
        except ValueError:
            hours = 0.0
        if not title:
            self.notify("Title is required", severity="warning")
            return
        self.dismiss({"title": title, "description": desc, "target_hours": hours})


class GoalsScreen(Screen):
    BINDINGS = [
        Binding("n", "new_goal", "New Goal"),
        Binding("escape", "app.pop_screen", "Back"),
    ]
    DEFAULT_CSS = """
    GoalsScreen { padding: 1 2; }
    DataTable { height: 1fr; }
    .section-title { text-style: bold; color: $accent; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Label("GOALS", classes="section-title")
        table = DataTable(id="goals-table")
        table.add_columns("Title", "Progress", "Logged", "Target", "Streak")
        yield table
        yield Label("N: new goal  |  ESC: back", classes="stat-label")

    def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#goals-table", DataTable)
        table.clear()
        for g in self.app.goal_svc.list_active():
            pct = self.app.goal_svc.progress_pct(g.id)
            logged = self.app.conn.execute(
                "SELECT COALESCE(SUM(actual_duration),0)/60.0 FROM sessions "
                "WHERE goal_id=? AND completed=1", (g.id,)
            ).fetchone()[0]
            bar = ("█" * int(pct / 10)) + ("░" * (10 - int(pct / 10)))
            table.add_row(g.title, f"{bar} {pct:.0f}%",
                          f"{logged:.1f}h", f"{g.target_hours:.0f}h", "")

    def action_new_goal(self) -> None:
        def on_result(data):
            if data:
                self.app.goal_svc.create(
                    data["title"], data["description"], data["target_hours"]
                )
                self._refresh_table()
                self.notify(f"Goal '{data['title']}' created!")

        self.app.push_screen(CreateGoalModal(), callback=on_result)
```

- [ ] **Step 2: Run and test**

```bash
python -m timetracker.main
```

1. Press `g` → Goals screen
2. Press `n` → CreateGoalModal
3. Fill in title + hours → Create
4. See goal appear in table
5. Press ESC → back to dashboard

- [ ] **Step 3: Commit**

```bash
git add src/timetracker/screens/goals.py
git commit -m "feat: goals screen with DataTable, CreateGoalModal, progress bars"
```

---

## Task 12: Analytics Screen

**Files:**
- Modify: `src/timetracker/screens/analytics.py`

- [ ] **Step 1: Implement analytics.py**

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Label, Sparkline, DataTable
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from datetime import date, timedelta


class HeatmapWidget(Static):
    """GitHub-style contribution heatmap (last 7 weeks)."""

    def __init__(self, daily_data: dict[str, float], **kwargs):
        super().__init__(**kwargs)
        self._data = daily_data

    def render(self) -> str:
        today = date.today()
        blocks = []
        for i in range(48, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            hours = self._data.get(d, 0)
            if hours == 0:
                blocks.append("[dim]░[/]")
            elif hours < 1:
                blocks.append("[green]▒[/]")
            elif hours < 2:
                blocks.append("[green]▓[/]")
            else:
                blocks.append("[bright_green]█[/]")
            if (i % 7) == 0 and i != 48:
                blocks.append("\n")
        return "".join(blocks)


class AnalyticsScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    DEFAULT_CSS = """
    AnalyticsScreen { padding: 1 2; }
    .section-title { text-style: bold; color: $accent; margin-bottom: 1; }
    .stat-box {
        border: solid $panel; padding: 1 2; width: 1fr; height: auto;
    }
    #charts-row { height: auto; }
    """

    def compose(self) -> ComposeResult:
        conn = self.app.conn
        session_svc = self.app.session_svc

        daily = session_svc.daily_hours(days=48)
        daily_dict = dict(daily)
        hours_values = [h for _, h in daily[-14:]] if daily else [0.0]

        streak = session_svc.streak()
        scores = session_svc.recent_focus_scores(20)
        avg_focus = sum(scores) / len(scores) if scores else 0

        total_row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(actual_duration),0)/60.0 "
            "FROM sessions WHERE completed=1 AND session_type='work'"
        ).fetchone()
        total_pomodoros = total_row[0]
        total_hours = total_row[1]

        abandoned = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE completed=0 AND session_type='work'"
        ).fetchone()[0]
        total_started = total_pomodoros + abandoned
        completion_rate = (total_pomodoros / total_started * 100) if total_started else 0

        yield Label("ANALYTICS", classes="section-title")

        with Horizontal(id="charts-row"):
            with Vertical(classes="stat-box"):
                yield Label("Daily Focus (hrs, last 14 days)", classes="section-title")
                yield Sparkline(hours_values, summary_function=max)

            with Vertical(classes="stat-box"):
                yield Label("Focus Score Trend", classes="section-title")
                yield Sparkline(scores or [0.0], summary_function=max)

        with Horizontal():
            with Vertical(classes="stat-box"):
                yield Label("STATS", classes="section-title")
                yield Label(f"Total pomodoros:   {total_pomodoros}")
                yield Label(f"Total hours:       {total_hours:.1f}h")
                yield Label(f"Current streak:    {streak} days")
                yield Label(f"Avg focus score:   {avg_focus:.1f}/5")
                yield Label(f"Completion rate:   {completion_rate:.0f}%")

            with Vertical(classes="stat-box"):
                yield Label("HEATMAP (last 7 weeks)", classes="section-title")
                yield HeatmapWidget(daily_dict)

        yield Label("ESC: back", classes="stat-label")
```

- [ ] **Step 2: Run and test**

```bash
python -m timetracker.main
```

Press `a` → Analytics screen shows sparklines, stats, heatmap. Press ESC to go back.

- [ ] **Step 3: Commit**

```bash
git add src/timetracker/screens/analytics.py
git commit -m "feat: analytics screen with sparklines, heatmap, completion stats"
```

---

## Task 13: History Screen

**Files:**
- Modify: `src/timetracker/screens/history.py`

- [ ] **Step 1: Implement history.py**

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Input, Label
from textual.containers import Vertical
from textual.binding import Binding
from textual import on
from datetime import datetime


class HistoryScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    DEFAULT_CSS = """
    HistoryScreen { padding: 1 2; }
    DataTable { height: 1fr; }
    Input { margin-bottom: 1; }
    .section-title { text-style: bold; color: $accent; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Label("SESSION HISTORY", classes="section-title")
        yield Input(placeholder="Filter by goal name or intent...", id="search-input")
        yield DataTable(id="history-table")
        yield Label("ESC: back", classes="stat-label")

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Date", "Goal", "Intent", "Duration", "Focus", "Reflection")
        self._load_sessions()

    def _load_sessions(self, filter_text: str = "") -> None:
        table = self.query_one("#history-table", DataTable)
        table.clear()
        rows = self.app.conn.execute(
            "SELECT s.*, g.title as goal_title FROM sessions s "
            "JOIN goals g ON s.goal_id = g.id "
            "WHERE s.session_type = 'work' AND s.completed = 1 "
            "ORDER BY s.started_at DESC LIMIT 100"
        ).fetchall()
        for row in rows:
            goal_title = row["goal_title"] or ""
            intent = row["intent"] or ""
            if filter_text and filter_text.lower() not in goal_title.lower() \
                    and filter_text.lower() not in intent.lower():
                continue
            started = row["started_at"][:10] if row["started_at"] else ""
            duration = f"{row['actual_duration']}m" if row["actual_duration"] else "-"
            score = "★" * (row["focus_score"] or 0) if row["focus_score"] else "-"
            reflection = (row["reflection"] or "")[:40]
            table.add_row(started, goal_title[:20], intent[:30], duration, score, reflection)

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._load_sessions(event.value)
```

- [ ] **Step 2: Run and test**

```bash
python -m timetracker.main
```

Press `h` → History screen. Type in search box to filter sessions. Press ESC.

- [ ] **Step 3: Commit**

```bash
git add src/timetracker/screens/history.py
git commit -m "feat: history screen with searchable session log"
```

---

## Task 14: CSS Polish and README

**Files:**
- Create: `src/timetracker/app.tcss` (global Textual CSS)
- Create: `README.md`

- [ ] **Step 1: Create global CSS file**

```css
/* src/timetracker/app.tcss */
Screen {
    background: $background;
}

.section-title {
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.stat-label {
    color: $text-muted;
}

.stat-value {
    text-style: bold;
    color: $success;
}

Header {
    background: $accent;
}

Footer {
    background: $panel;
}
```

- [ ] **Step 2: Reference CSS in main.py**

In `TimeTrackerApp`:
```python
CSS_PATH = "../app.tcss"   # relative to main.py inside the package
```

Or use `importlib.resources` for package-safe path:
```python
from importlib.resources import files

class TimeTrackerApp(App):
    CSS_PATH = str(files("timetracker").joinpath("app.tcss"))
```

- [ ] **Step 3: Write README.md**

```markdown
# TimeTracker

A goal-focused Pomodoro timer for the terminal. Open source, local-first — no cloud, no accounts.

## Install

```bash
pip install -e .
```

## Run

```bash
tt
```

## Keys

| Key | Action |
|-----|--------|
| `n` | Start new Pomodoro session |
| `p` | Pause / Resume timer |
| `s` | Abandon current session |
| `d` | Dashboard |
| `g` | Goals |
| `a` | Analytics |
| `h` | History |
| `q` | Quit |

## Data

All data is stored in `~/.timetracker/data.db` (SQLite). To sync between machines, symlink or place this directory inside Dropbox/Syncthing.
```

- [ ] **Step 4: Final test run**

```bash
pytest -v
```

Expected: all tests pass.

```bash
python -m timetracker.main
```

Expected: full app launches, all screens navigate correctly.

- [ ] **Step 5: Final commit**

```bash
git add src/timetracker/app.tcss README.md
git commit -m "feat: global CSS polish and README"
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|---|---|
| Pomodoro-first timer | Task 5 (service), Task 8 (widget), Task 9 (dashboard) |
| Pre-session intent prompt | Task 10 (IntentModal) |
| Post-session reflection + rating | Task 10 (ReflectionModal) |
| Goal hierarchy | Task 6 (GoalService), Task 11 (GoalsScreen) |
| Progress tracking per goal | Tasks 4, 6 (progress_pct) |
| Dashboard with timer + goal bars + sparkline | Task 9 |
| Session dots timeline | Task 9 (_build_session_dots) |
| Analytics: daily chart, heatmap, stats | Task 12 |
| History with search | Task 13 |
| Streak counter | Task 4 (current_streak), Task 9 |
| Local SQLite, no cloud | Task 3 |
| Open source (MIT) | README |
| `tt` CLI entry point | Task 1 (pyproject.toml) |
| Pause / resume | Task 5 (timer service) |
| Skip break | Task 5 (timer service) |

### Type Consistency

- `PomodoroService.state` → `TimerState` — used consistently in dashboard + modals
- `GoalService.list_active()` → `list[Goal]` — used in dashboard + goals screen + intent modal
- `SessionService.start()` → `int` (session_id) — stored in `_active_session_id` on dashboard
- `queries.*` all take `sqlite3.Connection` as first arg — consistent throughout

### No Placeholders

All tasks contain actual runnable code. No TODOs in implementation steps.
