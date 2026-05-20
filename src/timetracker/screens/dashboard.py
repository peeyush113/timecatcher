from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Dashboard — coming soon")
