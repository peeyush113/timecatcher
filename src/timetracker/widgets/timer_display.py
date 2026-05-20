from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from ..models import TimerStatus


class TimerDisplay(Widget):
    """Countdown timer with status label and pomodoro dot indicators."""

    DEFAULT_CSS = """
    TimerDisplay {
        height: 9;
        border: solid $accent;
        padding: 1 2;
        align: center middle;
        content-align: center middle;
    }
    #timer-label {
        color: $text-muted;
        width: 100%;
        content-align: center middle;
        text-align: center;
    }
    #timer-time {
        text-style: bold;
        color: $success;
        width: 100%;
        content-align: center middle;
        text-align: center;
    }
    #timer-time.break {
        color: $warning;
    }
    #timer-dots {
        width: 100%;
        content-align: center middle;
        text-align: center;
        color: $accent;
    }
    """

    seconds: reactive[int] = reactive(25 * 60)
    status: reactive[TimerStatus] = reactive(TimerStatus.IDLE)
    pomodoro_number: reactive[int] = reactive(1)
    intent: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("Ready — press N to start", id="timer-label")
        yield Label("25:00", id="timer-time")
        yield Label("◉ ○ ○ ○", id="timer-dots")

    def watch_seconds(self, seconds: int) -> None:
        mins, secs = divmod(seconds, 60)
        self.query_one("#timer-time", Label).update(f"{mins:02d}:{secs:02d}")

    def watch_status(self, status: TimerStatus) -> None:
        label = self.query_one("#timer-label", Label)
        time_widget = self.query_one("#timer-time", Label)
        status_map = {
            TimerStatus.IDLE: "Ready — press N to start",
            TimerStatus.INTENT: "Setting intent...",
            TimerStatus.RUNNING: f"Focus: {self.intent}" if self.intent else "Focusing...",
            TimerStatus.PAUSED: f"Paused — {self.intent}" if self.intent else "Paused",
            TimerStatus.BREAK: "Break time! ☕",
            TimerStatus.REFLECTION: "Session complete! ✓",
        }
        label.update(status_map.get(status, ""))
        if status == TimerStatus.BREAK:
            time_widget.add_class("break")
        else:
            time_widget.remove_class("break")

    def watch_pomodoro_number(self, num: int) -> None:
        dots = []
        for i in range(1, 5):
            if i < num:
                dots.append("●")
            elif i == num:
                dots.append("◉")
            else:
                dots.append("○")
        self.query_one("#timer-dots", Label).update("  ".join(dots))

    def watch_intent(self, intent: str) -> None:
        if self.status == TimerStatus.RUNNING:
            self.query_one("#timer-label", Label).update(f"Focus: {intent}")
