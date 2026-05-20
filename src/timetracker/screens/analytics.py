from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Sparkline, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from datetime import date, timedelta


class HeatmapWidget(Static):
    """7-week contribution heatmap using colored block characters."""

    def __init__(self, daily_data: dict[str, float], **kwargs):
        super().__init__(**kwargs)
        self._data = daily_data

    def render(self) -> str:
        today = date.today()
        lines = []
        # Build 7 rows (days of week), 7 columns (weeks)
        # Start from 48 days ago so we have ~7 weeks
        week_rows: list[list[str]] = [[] for _ in range(7)]
        for i in range(48, -1, -1):
            d = today - timedelta(days=i)
            hours = self._data.get(d.isoformat(), 0)
            day_of_week = d.weekday()  # 0=Mon, 6=Sun
            if hours == 0:
                block = "[dim]░[/dim]"
            elif hours < 1:
                block = "[green]▒[/green]"
            elif hours < 2:
                block = "[green]▓[/green]"
            else:
                block = "[bright_green]█[/bright_green]"
            week_rows[day_of_week].append(block)

        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, (label, row) in enumerate(zip(day_labels, week_rows)):
            lines.append(f"{label}  {'  '.join(row)}")
        return "\n".join(lines)


class AnalyticsScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back", show=True)]

    DEFAULT_CSS = """
    AnalyticsScreen {
        padding: 1 2;
    }
    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .stat-box {
        border: solid $panel;
        padding: 1 2;
        width: 1fr;
        height: auto;
        margin-right: 1;
    }
    .box-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .stat-line {
        color: $text;
        margin-bottom: 0;
    }
    .stat-value {
        text-style: bold;
        color: $success;
    }
    #charts-row {
        height: auto;
        margin-bottom: 1;
    }
    #stats-row {
        height: auto;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
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

        totals = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(actual_duration), 0) / 60.0 "
            "FROM sessions WHERE completed=1 AND session_type='work'"
        ).fetchone()
        total_pomodoros, total_hours = totals[0], totals[1]

        abandoned = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE completed=0 AND session_type='work'"
        ).fetchone()[0]
        total_started = total_pomodoros + abandoned
        completion_rate = (total_pomodoros / total_started * 100) if total_started else 0

        yield Label("ANALYTICS", id="screen-title")

        with Horizontal(id="charts-row"):
            with Vertical(classes="stat-box"):
                yield Label("Daily Focus — last 14 days (hrs)", classes="box-title")
                yield Sparkline(hours_values if hours_values else [0.0], summary_function=max)

            with Vertical(classes="stat-box"):
                yield Label("Focus Score Trend — last 20 sessions", classes="box-title")
                yield Sparkline(scores if scores else [0.0], summary_function=max)

        with Horizontal(id="stats-row"):
            with Vertical(classes="stat-box"):
                yield Label("STATS", classes="box-title")
                yield Label(f"Total pomodoros:    {total_pomodoros}", classes="stat-line")
                yield Label(f"Total hours:        {total_hours:.1f}h", classes="stat-line")
                yield Label(f"Current streak:     {streak} days", classes="stat-line")
                yield Label(f"Avg focus score:    {avg_focus:.1f} / 5", classes="stat-line")
                yield Label(f"Completion rate:    {completion_rate:.0f}%", classes="stat-line")

            with Vertical(classes="stat-box"):
                yield Label("HEATMAP — last 7 weeks", classes="box-title")
                yield HeatmapWidget(daily_dict)

        yield Label("ESC: back", id="hint")
