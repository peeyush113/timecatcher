from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Input, Label
from textual.containers import Vertical
from textual.binding import Binding
from textual import on


class HistoryScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back", show=True)]

    DEFAULT_CSS = """
    HistoryScreen {
        padding: 1 2;
    }
    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #search-input {
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("SESSION HISTORY", id="screen-title")
        yield Input(placeholder="Filter by goal or intent...", id="search-input")
        table = DataTable(id="history-table", zebra_stripes=True)
        table.add_columns("Date", "Goal", "Intent", "Duration", "Focus", "Reflection")
        yield table
        yield Label("Type to filter  |  ESC: back", id="hint")

    def on_mount(self) -> None:
        self._load_sessions()

    def _load_sessions(self, filter_text: str = "") -> None:
        table = self.query_one("#history-table", DataTable)
        table.clear()
        rows = self.app.conn.execute(
            "SELECT s.*, g.title as goal_title "
            "FROM sessions s JOIN goals g ON s.goal_id = g.id "
            "WHERE s.session_type = 'work' AND s.completed = 1 "
            "ORDER BY s.started_at DESC LIMIT 200"
        ).fetchall()
        for row in rows:
            goal_title = row["goal_title"] or ""
            intent = row["intent"] or ""
            if filter_text:
                needle = filter_text.lower()
                if needle not in goal_title.lower() and needle not in intent.lower():
                    continue
            started = row["started_at"][:10] if row["started_at"] else "—"
            duration = f"{row['actual_duration']}m" if row["actual_duration"] else "—"
            score = "★" * (row["focus_score"] or 0) if row["focus_score"] else "—"
            reflection = (row["reflection"] or "")[:45]
            table.add_row(
                started,
                goal_title[:22],
                intent[:32],
                duration,
                score,
                reflection,
            )

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._load_sessions(event.value)
