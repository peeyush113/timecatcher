from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import DataTable, Button, Input, Label
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual import on


class CreateGoalModal(ModalScreen):
    """Modal form to create a new goal."""

    DEFAULT_CSS = """
    CreateGoalModal {
        align: center middle;
    }
    #goal-dialog {
        width: 62;
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
    .field-label {
        color: $text-muted;
        margin-top: 1;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="goal-dialog"):
            yield Label("New Goal", classes="modal-title")
            yield Label("Title *", classes="field-label")
            yield Input(placeholder="e.g. Write my thesis", id="title-input")
            yield Label("Description (optional)", classes="field-label")
            yield Input(placeholder="What is this goal about?", id="desc-input")
            yield Label("Target hours (0 = no target)", classes="field-label")
            yield Input(placeholder="e.g. 50", value="0", id="hours-input")
            with Horizontal():
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return

        title = self.query_one("#title-input", Input).value.strip()
        desc = self.query_one("#desc-input", Input).value.strip()
        hours_str = self.query_one("#hours-input", Input).value.strip()

        if not title:
            self.notify("Title is required", severity="warning")
            return

        try:
            hours = float(hours_str) if hours_str else 0.0
        except ValueError:
            self.notify("Target hours must be a number", severity="warning")
            return

        self.dismiss({"title": title, "description": desc, "target_hours": hours})


class GoalsScreen(Screen):
    BINDINGS = [
        Binding("n", "new_goal", "New Goal", show=True),
        Binding("escape", "app.pop_screen", "Back", show=True),
    ]

    DEFAULT_CSS = """
    GoalsScreen {
        padding: 1 2;
    }
    #screen-title {
        text-style: bold;
        color: $accent;
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
        yield Label("GOALS", id="screen-title")
        table = DataTable(id="goals-table", zebra_stripes=True)
        table.add_columns("Title", "Progress", "Logged", "Target")
        yield table
        yield Label("N: new goal  |  ESC: back to dashboard", id="hint")

    def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#goals-table", DataTable)
        table.clear()
        for g in self.app.goal_svc.list_active():
            pct = self.app.goal_svc.progress_pct(g.id)
            logged = self.app.conn.execute(
                "SELECT COALESCE(SUM(actual_duration), 0) / 60.0 "
                "FROM sessions WHERE goal_id=? AND completed=1",
                (g.id,),
            ).fetchone()[0]
            filled = int(pct / 10)
            bar = "█" * filled + "░" * (10 - filled)
            table.add_row(
                g.title,
                f"{bar} {pct:.0f}%",
                f"{logged:.1f}h",
                f"{g.target_hours:.0f}h" if g.target_hours else "—",
            )

    def action_new_goal(self) -> None:
        def on_result(data):
            if data:
                self.app.goal_svc.create(
                    data["title"],
                    description=data["description"],
                    target_hours=data["target_hours"],
                )
                self._refresh_table()
                self.notify(f"Goal '{data['title']}' created!", severity="information")

        self.app.push_screen(CreateGoalModal(), callback=on_result)
