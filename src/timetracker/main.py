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
    TITLE = "timecatcher"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        Binding("d", "push_screen('dashboard')", "Dashboard", show=True),
        Binding("g", "push_screen('goals')", "Goals", show=True),
        Binding("a", "push_screen('analytics')", "Analytics", show=True),
        Binding("h", "push_screen('history')", "History", show=True),
        Binding("n", "new_session", "New Session", show=True),
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

    def action_new_session(self) -> None:
        screen = self.screen
        if hasattr(screen, "action_new_session"):
            screen.action_new_session()


def main() -> None:
    TimeTrackerApp().run()


if __name__ == "__main__":
    main()
