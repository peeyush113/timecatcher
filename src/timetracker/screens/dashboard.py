from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, ProgressBar, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding

from ..models import TimerStatus
from ..widgets.timer_display import TimerDisplay
from ..widgets.sparkline import FocusSparkline


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
        Binding("s", "stop_session", "Stop", show=True),
    ]

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
        padding: 1 2;
    }
    #goals-panel {
        border: solid $panel;
        padding: 1 2;
    }
    #bottom-panel {
        border: solid $panel;
        padding: 1 2;
    }
    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .stat-value {
        text-style: bold;
        color: $success;
    }
    .stat-label {
        color: $text-muted;
    }
    .goal-row {
        height: 3;
        margin-bottom: 1;
    }
    .goal-title {
        width: 28;
        content-align: left middle;
    }
    .goal-hours {
        width: 12;
        color: $text-muted;
        content-align: left middle;
    }
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
            yield Label(
                f"Today: {summary['completed_pomodoros']} pomodoros  "
                f"({summary['total_minutes']}m)",
                classes="stat-label",
            )

        with Vertical(id="goals-panel"):
            yield Label("TODAY'S GOALS", classes="section-title")
            goals = app.goal_svc.list_active()
            if goals:
                for g in goals[:5]:
                    pct = app.goal_svc.progress_pct(g.id)
                    logged = app.conn.execute(
                        "SELECT COALESCE(SUM(actual_duration), 0) / 60.0 "
                        "FROM sessions WHERE goal_id=? AND completed=1",
                        (g.id,),
                    ).fetchone()[0]
                    with Horizontal(classes="goal-row"):
                        yield Label(g.title[:26], classes="goal-title")
                        bar = ProgressBar(total=100, show_percentage=False, show_eta=False)
                        bar.advance(pct)
                        yield bar
                        yield Label(f" {logged:.1f}/{g.target_hours:.0f}h", classes="goal-hours")
            else:
                yield Label("No goals yet — press G to create one", classes="stat-label")

        with Vertical(id="bottom-panel"):
            yield Label("FOCUS TREND", classes="section-title")
            yield FocusSparkline(scores)
            yield Label("")
            yield Label("SESSION TIMELINE", classes="section-title")
            dots = self._build_session_dots(summary["sessions"])
            yield Label(dots if dots else "No sessions today", classes="stat-label")

    def _build_session_dots(self, sessions) -> str:
        parts = []
        for s in sessions:
            if s["session_type"] != "work":
                continue
            if s["completed"]:
                score = s["focus_score"] or 3
                color = {1: "red", 2: "orange3", 3: "yellow", 4: "green", 5: "bright_cyan"}.get(score, "white")
                parts.append(f"[{color}]●[/]")
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
            ReflectionModal(
                self.app.timer_svc,
                self.app.session_svc,
                self._active_session_id,
            )
        )

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

    def action_toggle_pause(self) -> None:
        state = self.app.timer_svc.state
        try:
            if state.status == TimerStatus.RUNNING:
                self.app.timer_svc.pause()
            elif state.status == TimerStatus.PAUSED:
                self.app.timer_svc.resume()
        except ValueError:
            pass

    def action_stop_session(self) -> None:
        try:
            self.app.timer_svc.abandon()
            self._active_session_id = None
        except ValueError:
            pass
